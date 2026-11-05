"""Anonimización antes de analizar o guardar transcripciones.

Si está instalado DataShield (`datashield-es`, detector de datos personales de
Colombia/LatAm con validación de NIT, Luhn, etc.) se usa ese motor. Si no, se
aplica un anonimizador mínimo incorporado que cubre lo más frecuente en call
center: correos, teléfonos, cédulas/números largos, tarjetas y direcciones.

El análisis de Alómetro no necesita los datos personales: solo el *tipo* de dato
(«el cliente dio su cédula»), así que las etiquetas no afectan la evaluación.
"""

from __future__ import annotations

import re
from dataclasses import replace

from .modelos import Conversacion, Turno
from .texto import luhn_valido

try:  # pragma: no cover - depende del entorno
    from datashield_es import anonymize as _ds_anonymize  # type: ignore

    MOTOR = "datashield"
except Exception:  # pragma: no cover
    _ds_anonymize = None
    MOTOR = "basico"

_CORREO = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")
_TARJETA = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_TELEFONO = re.compile(r"(?<!\d)(\+?57[ -]?)?(3\d{2}[ -]?\d{3}[ -]?\d{4}|60\d[ -]?\d{3}[ -]?\d{4})(?!\d)")
_NUMERO_LARGO = re.compile(r"(?<![\w$])(\d{1,3}(\.\d{3}){2,3}|\d{6,12})(?![\w])")
_DIRECCION = re.compile(
    r"\b(calle|cll|carrera|cra|kr|avenida|av|diagonal|dg|transversal|tv)\.?\s*\d+[a-z]?\s*(bis)?\s*(#|no\.?|n°|numero)\s*\d+[a-z]?\s*-\s*\d+",
    re.IGNORECASE,
)


def _basico(texto: str) -> str:
    texto = _CORREO.sub("[CORREO]", texto)
    texto = _DIRECCION.sub("[DIRECCION]", texto)

    def _tarjeta(m: re.Match) -> str:
        return "[TARJETA]" if luhn_valido(m.group(0)) else m.group(0)

    texto = _TARJETA.sub(_tarjeta, texto)
    texto = _TELEFONO.sub("[TELEFONO]", texto)
    texto = _NUMERO_LARGO.sub("[NUMERO]", texto)
    return texto


def anonimizar_texto(texto: str, motor: str | None = None) -> str:
    motor = motor or MOTOR
    if motor == "datashield" and _ds_anonymize is not None:
        return _ds_anonymize(texto)
    return _basico(texto)


def anonimizar(conv: Conversacion, motor: str | None = None) -> Conversacion:
    """Copia de la conversación con los textos anonimizados.

    Los radicados (CUN, número de caso) se conservan porque son evidencia de
    cumplimiento y no identifican a la persona.
    """
    turnos = []
    for t in conv.turnos:
        protegido, marcas = _proteger_radicados(t.texto)
        limpio = anonimizar_texto(protegido, motor)
        for clave, valor in marcas.items():
            limpio = limpio.replace(clave, valor)
        turnos.append(Turno(rol=t.rol, texto=limpio, t=t.t))
    return replace(conv, turnos=turnos)


_RADICADO = re.compile(
    r"\b(radicado|cun|caso|ticket|solicitud|seguimiento|pedido|orden)\b(\D{0,25}?)([A-Za-z0-9-]*\d{4,}[A-Za-z0-9-]*)",
    re.IGNORECASE,
)


def _proteger_radicados(texto: str) -> tuple[str, dict[str, str]]:
    marcas: dict[str, str] = {}

    def _sub(m: re.Match) -> str:
        clave = f"RADQZ{len(marcas)}QZ"
        marcas[clave] = m.group(3)
        return f"{m.group(1)}{m.group(2)}{clave}"

    return _RADICADO.sub(_sub, texto), marcas
