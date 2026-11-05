"""Roles de transcripciones reales: «SPEAKER_00», «Hablante 1», «spk_1», «A»/«B»…

Los motores de voz a texto con diarización (Whisper + pyannote, AWS Transcribe,
Google STT, Azure) separan hablantes pero no saben quién es el agente. Alómetro
lo infiere por lo que cada hablante dice: quien se presenta, saluda en nombre de
la empresa, indaga, verifica identidad o pide datos es el agente; el resto,
cliente. La inferencia queda registrada en `metadatos["roles_inferidos"]` y se
puede fijar a mano con un mapa (CLI: ``--roles SPEAKER_00=agente,SPEAKER_01=cliente``).
"""

from __future__ import annotations

import re

from . import lexicos as L
from .modelos import ROLES, normalizar_rol
from .texto import buscar, contar, normalizar

_PRIMERA_PERSONA = re.compile(r"\b(mi|mis|tengo|quiero|necesito|me cobraron|no me|yo)\b")
_PIDE_SERVICIO = re.compile(r"\b(quiero|quisiera|deseo|necesito|voy a|cancelen|cancele|ayudeme|me ayuda|me pueden|me puede|me dicen)\b")
_PREGUNTA_CLIENTE = re.compile(r"^\W*(hola,? )?(a que hora|cual|cuando|como|donde|por que|porque|cuanto|que paso|me pueden|me puede|hay|tienen)\b")
_TRATO_USTED = re.compile(r"\b(usted|su|sus|senora|senor|sumerce|le)\b")


def rol_conocido(etiqueta: str) -> str | None:
    try:
        return normalizar_rol(etiqueta)
    except ValueError:
        return None


def leer_mapa(texto: str | None) -> dict[str, str]:
    """«SPEAKER_00=agente,SPEAKER_01=cliente» -> dict (valida los roles)."""
    mapa: dict[str, str] = {}
    for par in (texto or "").split(","):
        if not par.strip():
            continue
        if "=" not in par:
            raise ValueError(f"Mapa de roles inválido: {par!r}. Use ETIQUETA=rol, p. ej. SPEAKER_00=agente.")
        k, v = (x.strip() for x in par.split("=", 1))
        rol = rol_conocido(v)
        if rol is None:
            raise ValueError(f"Rol desconocido {v!r} para {k!r}. Use uno de {ROLES}.")
        mapa[k.lower()] = rol
    return mapa


def puntaje_agente(textos: list[str]) -> float:
    """Positivo = habla como agente; negativo = habla como cliente."""
    p = 0.0
    for i, t in enumerate(textos):
        n = normalizar(t)
        for patrones, peso in ((L.IDENTIFICACION_AGENTE, 3), (L.INDAGACION, 2), (L.VERIFICACION, 2), (L.AVISO_GRABACION, 3),
                               (L.RESUMEN, 1), (L.AYUDA_ADICIONAL, 2), (L.APROPIACION, 1), (L.TRANSFERENCIA, 2), (L.ESPERA, 1)):
            if buscar(patrones, n):
                p += peso
        if i < 2 and buscar(L.SALUDO, n):
            p += 1
        if any(pat.search(n) for pats in L.DATOS.values() for pat in pats):
            p += 2
        if buscar(L.QUEJA_CLIENTE, n) or buscar(L.PETICION_HUMANO, n):
            p -= 3
        p -= 1.5 * min(2, contar(L.FRUSTRACION_FUERTE, n) + contar(L.FRUSTRACION_MEDIA, n))
        p -= 0.5 * len(_PRIMERA_PERSONA.findall(n))
        p -= 1.0 * min(2, len(_PIDE_SERVICIO.findall(n)))
        if _PREGUNTA_CLIENTE.search(n):
            p -= 1.5
        p += 0.5 * min(3, len(_TRATO_USTED.findall(n)))
    return p / max(1, len(textos)) ** 0.5


UMBRAL_CONFIANZA = 1.5  # diferencia mínima de puntaje entre el «agente» y el siguiente hablante


def resolver(etiquetas: list[str], textos: list[str], mapa: dict[str, str] | None = None) -> tuple[list[str], dict[str, str]]:
    """Devuelve (rol de cada turno, roles inferidos por etiqueta)."""
    mapa = {k.lower(): v for k, v in (mapa or {}).items()}
    fijos: dict[str, str] = {}
    desconocidas: list[str] = []
    for e in etiquetas:
        clave = e.strip().lower()
        if clave in fijos or clave in desconocidas:
            continue
        rol = mapa.get(clave) or rol_conocido(e)
        if rol:
            fijos[clave] = rol
        else:
            desconocidas.append(clave)
    inferidos: dict[str, str] = {}
    if desconocidas:
        por_etiqueta = {k: [t for e, t in zip(etiquetas, textos) if e.strip().lower() == k] for k in desconocidas}
        puntajes = {k: puntaje_agente(v) for k, v in por_etiqueta.items()}
        ya_hay_agente = "agente" in fijos.values()
        orden = sorted(desconocidas, key=lambda k: (-puntajes[k], desconocidas.index(k)))
        for k in orden:
            if not ya_hay_agente and k == orden[0] and (puntajes[k] > 0 or len(desconocidas) > 1):
                inferidos[k] = "agente"
            else:
                inferidos[k] = "cliente"
        if len(orden) >= 2 and puntajes[orden[0]] - puntajes[orden[1]] < UMBRAL_CONFIANZA:
            inferidos["_confianza"] = "baja"
    todos = {**fijos, **inferidos}
    return [todos[e.strip().lower()] for e in etiquetas], dict(inferidos)
