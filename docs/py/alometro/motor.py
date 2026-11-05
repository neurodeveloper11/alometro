"""Motor de evaluación: conversación -> señales -> rúbrica -> evaluación."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .detectores import Senales, analizar
from .modelos import Conversacion, Evaluacion, Evidencia, ResultadoCriterio
from .privacidad import anonimizar_texto
from .rubrica import CRITERIOS, DIMENSIONES, Criterio

NIVELES = ((90, "Excelente"), (75, "Bueno"), (60, "Mejorable"), (0, "Deficiente"))


@dataclass
class Politica:
    """Opciones de evaluación que cada operación puede ajustar."""

    anular_por_critico: bool = True
    anonimizar_evidencias: bool = True
    pesos: dict[str, int] = field(default_factory=dict)  # id de criterio -> peso
    desactivar: set[str] = field(default_factory=set)  # ids de criterios a omitir


def nivel_de(puntaje: int, hay_critico: bool) -> str:
    if hay_critico:
        return "Crítico"
    for minimo, nombre in NIVELES:
        if puntaje >= minimo:
            return nombre
    return "Deficiente"


def _limpiar(ev: list[Evidencia], anonimizar: bool) -> list[Evidencia]:
    if not anonimizar:
        return ev
    return [Evidencia(turno=e.turno, rol=e.rol, cita=anonimizar_texto(e.cita)) for e in ev]


def evaluar(conv: Conversacion, politica: Politica | None = None, criterios: Iterable[Criterio] = CRITERIOS) -> Evaluacion:
    politica = politica or Politica()
    if not any(t.texto for t in conv.turnos):
        raise ValueError(f"La conversación {conv.id!r} no tiene turnos con texto: no hay nada que evaluar.")
    s: Senales = analizar(conv)
    resultados: list[ResultadoCriterio] = []
    for cr in criterios:
        if cr.id in politica.desactivar:
            continue
        aplica, cumple, detalle, ev = cr.evaluar(conv, s)
        resultados.append(ResultadoCriterio(
            id=cr.id, nombre=cr.nombre, dimension=cr.dimension, peso=politica.pesos.get(cr.id, cr.peso),
            critico=cr.critico, aplica=aplica, cumple=cumple if aplica else None, detalle=detalle,
            evidencias=_limpiar(ev, politica.anonimizar_evidencias),
            recomendacion=cr.recomendacion if aplica and cumple is False else "",
        ))

    puntuables = [r for r in resultados if r.aplica and r.peso > 0]
    total = sum(r.peso for r in puntuables)
    obtenido = sum(r.peso for r in puntuables if r.cumple)
    base = round(100 * obtenido / total) if total else 100

    dimensiones: dict[str, int | None] = {}
    for d in DIMENSIONES:
        rs = [r for r in puntuables if r.dimension == d]
        t = sum(r.peso for r in rs)
        dimensiones[d] = round(100 * sum(r.peso for r in rs if r.cumple) / t) if t else None

    criticos = [
        {"criterio": r.id, "nombre": r.nombre, "categoria": r.critico, "detalle": r.detalle,
         "evidencias": [e.a_dict() for e in r.evidencias]}
        for r in resultados if r.critico and r.aplica and r.cumple is False
    ]
    puntaje = 0 if (criticos and politica.anular_por_critico) else base

    fallas = sorted((r for r in resultados if r.aplica and r.cumple is False),
                    key=lambda r: (r.critico is None, -r.peso))
    recomendaciones = [f"[{r.id}] {r.recomendacion}" for r in fallas][:5]

    senales = s.resumen()  # sin texto del cliente: no requiere anonimizar
    senales["hubo_bot"], senales["hubo_agente"] = conv.hubo_bot, conv.hubo_agente
    senales["turnos"] = len(conv.turnos)
    return Evaluacion(
        conversacion_id=conv.id, tipo=conv.tipo, canal=conv.canal, sector=conv.sector, direccion=conv.direccion,
        agente_id=conv.agente_id, cliente_id=conv.cliente_id,
        inicio=conv.inicio.isoformat() if conv.inicio else None,
        puntaje_base=base, puntaje=puntaje, nivel=nivel_de(base, bool(criticos)),
        errores_criticos=criticos, criterios=resultados, senales=senales,
        dimensiones=dimensiones, recomendaciones=recomendaciones,
    )


def evaluar_lote(convs: Iterable[Conversacion], politica: Politica | None = None,
                 omitidas: list[str] | None = None) -> list[Evaluacion]:
    """Evalúa todas las conversaciones; las vacías se omiten y su id se agrega a `omitidas`."""
    res = []
    for c in convs:
        if not any(t.texto for t in c.turnos):
            if omitidas is not None:
                omitidas.append(c.id)
            continue
        res.append(evaluar(c, politica))
    return res
