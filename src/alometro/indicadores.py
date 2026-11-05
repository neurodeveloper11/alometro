"""Indicadores de resultado: ¿la operación está logrando el objetivo?

El objetivo de Alómetro no es «poner notas»: es que el cliente **resuelva**, con
**poco esfuerzo**, **sin quedar atrapado en un bot** y **sin abusos**. Cada
indicador declara su fórmula, su meta, el sentido deseado y su intervalo de
confianza del 95 %, para no confundir ruido con mejora.

Las metas por defecto son **puntos de partida**: deben ajustarse con la línea
base de cada operación (mida 4 semanas antes de fijarlas).
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta

from .calendario import a_hora_colombia
from .coaching import plan_coaching
from .estadistica import diferencia_medias, diferencia_proporciones, wilson
from .modelos import Evaluacion


@dataclass
class Indicador:
    id: str
    nombre: str
    formula: str
    sentido: str  # "mayor" (más es mejor) | "menor"
    meta: float
    unidad: str  # "%" | "pts" | "pasos" | "n"
    por_que: str
    valor: float | None = None
    n: int = 0
    x: int = 0
    ic95: tuple[float, float] | None = None
    estado: str = "sin_datos"
    muestras: list[float] = field(default_factory=list, repr=False)

    def a_dict(self) -> dict:
        d = asdict(self)
        d.pop("muestras")
        return d


def _fecha(e: Evaluacion) -> datetime | None:
    return a_hora_colombia(datetime.fromisoformat(e.inicio)) if e.inicio else None


def _criterio(e: Evaluacion, cid: str):
    return next((c for c in e.criterios if c.id == cid), None)


def recontactos(evs: list[Evaluacion], dias: int = 7) -> dict[str, bool | None]:
    """Para cada evaluación: ¿el mismo cliente volvió a contactar dentro de `dias`?

    None = no se puede saber (sin cliente/fecha, o la ventana de observación
    queda fuera del periodo de datos: censura a la derecha).
    """
    con_fecha = [(e, _fecha(e)) for e in evs if e.cliente_id and e.inicio]
    if not con_fecha:
        return {e.conversacion_id: None for e in evs}
    fin_datos = max(f for _, f in con_fecha)
    por_cliente: dict[str, list[tuple[datetime, Evaluacion]]] = defaultdict(list)
    for e, f in con_fecha:
        por_cliente[e.cliente_id].append((f, e))
    res: dict[str, bool | None] = {e.conversacion_id: None for e in evs}
    ventana = timedelta(days=dias)
    for lista in por_cliente.values():
        lista.sort(key=lambda x: x[0])
        for i, (f, e) in enumerate(lista):
            if e.tipo in ("ventas", "cobranza") or e.direccion == "saliente":
                continue  # el recontacto mide contactos que inicia el cliente
            siguientes = [g for g, o in lista[i + 1:] if o.direccion == "entrante" and g - f <= ventana]
            if siguientes:
                res[e.conversacion_id] = True
            elif f + ventana <= fin_datos:
                res[e.conversacion_id] = False
    return res


def frecuencia_ley_2300(evs: list[Evaluacion]) -> list[dict]:
    """Clientes contactados (salientes de cobranza/ventas) más de una vez el mismo
    día o por más de un canal en la misma semana (Ley 2300 de 2023, art. 3)."""
    por_cliente: dict[str, list[tuple[datetime, Evaluacion]]] = defaultdict(list)
    for e in evs:
        if e.direccion == "saliente" and e.tipo in ("cobranza", "ventas") and e.cliente_id and e.inicio:
            por_cliente[e.cliente_id].append((_fecha(e), e))
    alertas = []
    for cliente, lista in por_cliente.items():
        dias: dict = defaultdict(list)
        semanas: dict = defaultdict(set)
        for f, e in lista:
            dias[f.date()].append(e.conversacion_id)
            semanas[tuple(f.isocalendar())[:2]].add(e.canal)
        for d, ids in dias.items():
            if len(ids) > 1:
                alertas.append({"cliente_id": cliente, "regla": "más de un contacto el mismo día", "fecha": d.isoformat(), "conversaciones": ids})
        for (anio, sem), canales in semanas.items():
            if len(canales) > 1:
                alertas.append({"cliente_id": cliente, "regla": "varios canales en la misma semana", "semana": f"{anio}-S{sem:02d}", "canales": sorted(canales)})
    return alertas


def _prop(id_, nombre, formula, sentido, meta, por_que, poblacion, exito) -> Callable[[list[Evaluacion], dict], Indicador]:
    def calc(evs: list[Evaluacion], ctx: dict) -> Indicador:
        ind = Indicador(id_, nombre, formula, sentido, meta, "%", por_que)
        base = [e for e in evs if poblacion(e, ctx)]
        ind.n = len(base)
        ind.x = sum(1 for e in base if exito(e, ctx))
        if ind.n:
            ind.valor = ind.x / ind.n
            ind.ic95 = wilson(ind.x, ind.n)
            ok = ind.valor >= meta if sentido == "mayor" else ind.valor <= meta
            ind.estado = "cumple" if ok else "no_cumple"
        return ind
    return calc


def _media(id_, nombre, formula, sentido, meta, unidad, por_que, poblacion, valor, mediana=False):
    def calc(evs: list[Evaluacion], ctx: dict) -> Indicador:
        ind = Indicador(id_, nombre, formula, sentido, meta, unidad, por_que)
        xs = [float(v) for e in evs if poblacion(e, ctx) and (v := valor(e, ctx)) is not None]
        ind.n, ind.muestras = len(xs), xs
        if xs:
            ind.valor = statistics.median(xs) if mediana else statistics.fmean(xs)
            if len(xs) >= 2 and not mediana:
                se = statistics.stdev(xs) / len(xs) ** 0.5
                ind.ic95 = (ind.valor - 1.96 * se, ind.valor + 1.96 * se)
            ok = ind.valor >= meta if sentido == "mayor" else ind.valor <= meta
            ind.estado = "cumple" if ok else "no_cumple"
        return ind
    return calc


def _s(e: Evaluacion, k: str):
    return e.senales.get(k)


def _sin_critico(cat: str):
    return lambda e, c: not any(x["categoria"] == cat for x in e.errores_criticos)


TODOS = lambda e, c: True
ATENCION = lambda e, c: e.tipo != "ventas"
CON_BOT = lambda e, c: bool(_s(e, "hubo_bot"))
SOLO_BOT = lambda e, c: bool(_s(e, "hubo_bot")) and not _s(e, "hubo_agente")

INDICADORES = [
    _prop("I01", "Resolución en el contacto", "resueltas o radicadas con plazo / interacciones de atención", "mayor", 0.70,
          "Es el objetivo principal: que el cliente salga con su problema resuelto o con un compromiso concreto.",
          ATENCION, lambda e, c: (cr := _criterio(e, "R1")) is not None and cr.cumple is True),
    _prop("I02", "Recontacto en 7 días", "clientes que vuelven a contactar en 7 días / interacciones observables", "menor", 0.15,
          "La prueba real de la resolución: si el cliente vuelve, no se resolvió (aunque la conversación lo pareciera).",
          lambda e, c: c["recontacto"].get(e.conversacion_id) is not None, lambda e, c: c["recontacto"][e.conversacion_id] is True),
    _prop("I03", "Peticiones de humano atendidas", "transferidas a una persona / conversaciones de bot donde se pidió", "mayor", 0.95,
          "Responde a la queja central de la gente: «quiero hablar con una persona».",
          lambda e, c: CON_BOT(e, c) and (_s(e, "peticiones_humano") or 0) > 0, lambda e, c: _s(e, "humano_atendido") is True),
    _media("I04", "Respuestas del bot hasta la persona", "mediana de respuestas del bot entre la petición y la persona", "menor", 2, "pasos",
           "Cada respuesta extra del bot después de pedir una persona aumenta la frustración.",
           lambda e, c: _s(e, "pasos_bot_hasta_humano") is not None, lambda e, c: _s(e, "pasos_bot_hasta_humano"), mediana=True),
    _prop("I05", "Bucles del bot", "conversaciones con bucle / conversaciones con bot", "menor", 0.05,
          "El bucle sin salida es la experiencia que hace sentir que «el servicio al cliente no sirve».",
          CON_BOT, lambda e, c: bool(_s(e, "bucle_bot"))),
    _prop("I06", "Contención falsa", "conversaciones solo-bot sin solución o con recontacto / conversaciones solo-bot", "menor", 0.10,
          "Separa la contención real (el bot resolvió) de la aparente (el cliente se rindió o volvió por otro canal).",
          SOLO_BOT, lambda e, c: ((cr := _criterio(e, "B5")) is not None and cr.cumple is False) or c["recontacto"].get(e.conversacion_id) is True),
    _prop("I07", "Pérdida de contexto", "conversaciones donde se repidieron datos / conversaciones con traspaso", "menor", 0.10,
          "Escalar sin perder el contexto es lo que más valoran los usuarios de chatbots bancarios en Colombia (63 %, Delto 2025).",
          lambda e, c: (bool(_s(e, "hubo_bot")) and bool(_s(e, "hubo_agente"))) or (_s(e, "transferencias") or 0) > 0,
          lambda e, c: (_s(e, "datos_repedidos") or 0) > 0),
    _prop("I08", "Desescalada de clientes frustrados", "clientes que terminan menos frustrados / clientes que empezaron frustrados", "mayor", 0.60,
          "Mide si la atención calma o enciende. Es la competencia humana que un bot no reemplaza.",
          lambda e, c: (cr := _criterio(e, "T6")) is not None and cr.aplica, lambda e, c: _criterio(e, "T6").cumple is True),
    _prop("I09", "Frustración que escala", "conversaciones donde la frustración sube / conversaciones con 2+ turnos del cliente", "menor", 0.10,
          "La conversación no debería empeorar el ánimo del cliente.",
          lambda e, c: _s(e, "trayectoria_emocional") != "sin_datos", lambda e, c: _s(e, "trayectoria_emocional") == "escalada"),
    _prop("I10", "Libre de error crítico: cliente", "interacciones sin error crítico de cliente / total", "mayor", 0.95,
          "Callejón sin salida, humano negado, irrespeto o contención falsa.", TODOS, _sin_critico("cliente")),
    _prop("I11", "Libre de error crítico: negocio", "interacciones sin error crítico de negocio / total", "mayor", 0.97,
          "Ventas sin aceptación expresa, petición de claves u OTP.", TODOS, _sin_critico("negocio")),
    _prop("I12", "Libre de error crítico: cumplimiento", "interacciones sin error crítico normativo / total", "mayor", 0.99,
          "Ley 2300, Ley 1480, Res. CRC 8171: cada falla es una posible sanción.", TODOS, _sin_critico("cumplimiento")),
    _prop("I13", "Esfuerzo alto del cliente", "interacciones con esfuerzo ≥ 5 de 10 / total", "menor", 0.15,
          "Transferencias, esperas, desvíos y repeticiones. El esfuerzo del cliente se asocia con la deslealtad (Dixon, Freeman y Toman, HBR 2010).",
          TODOS, lambda e, c: (_s(e, "esfuerzo") or 0) >= 5),
    _prop("I14", "Amenaza de queja externa", "interacciones con mención de SIC, tutela, abogado o redes / total", "menor", 0.03,
          "Anticipa quejas ante la SIC, la Superfinanciera o la CRC y crisis en redes.",
          TODOS, lambda e, c: bool(_s(e, "amenaza_externa"))),
    _prop("I15", "Abandono sin solución", "interacciones donde el cliente se va frustrado o pidiendo humano / total", "menor", 0.05,
          "El cliente que se va sin solución no siempre se queja: simplemente se va.",
          TODOS, lambda e, c: bool(_s(e, "abandono"))),
    _media("I16", "Puntaje de calidad promedio", "promedio del puntaje final (0-100)", "mayor", 80, "pts",
           "Resume el cumplimiento de la rúbrica, con los errores críticos anulando la nota.",
           TODOS, lambda e, c: e.puntaje),
]


def calcular(evs: list[Evaluacion], dias_recontacto: int = 7, metas: dict[str, float] | None = None) -> dict:
    ctx = {"recontacto": recontactos(evs, dias_recontacto)}
    inds = [f(evs, ctx) for f in INDICADORES]
    if metas:
        for ind in inds:
            if ind.id in metas:
                ind.meta = metas[ind.id]
                if ind.valor is not None:
                    ok = ind.valor >= ind.meta if ind.sentido == "mayor" else ind.valor <= ind.meta
                    ind.estado = "cumple" if ok else "no_cumple"
    solo_bot = [e for e in evs if SOLO_BOT(e, ctx)]
    con_bot = [e for e in evs if CON_BOT(e, ctx)]
    reales = [e for e in solo_bot if (cr := _criterio(e, "B5")) is not None and cr.cumple
              and ctx["recontacto"].get(e.conversacion_id) is not True]
    contencion = {
        "conversaciones_con_bot": len(con_bot),
        "contencion_bruta": (len(solo_bot) / len(con_bot)) if con_bot else None,
        "contencion_real": (len(reales) / len(con_bot)) if con_bot else None,
    }
    return {
        "n": len(evs),
        "indicadores": inds,
        "contencion": contencion,
        "ley_2300_frecuencia": frecuencia_ley_2300(evs),
        "agentes": por_agente(evs),
        "coaching": plan_coaching(evs),
        "temas": por_tema(evs),
        "por_modalidad": por_modalidad(evs),
        "criterios": por_criterio(evs),
    }


def por_agente(evs: list[Evaluacion]) -> list[dict]:
    grupos: dict[str, list[Evaluacion]] = defaultdict(list)
    for e in evs:
        if e.agente_id and _s(e, "hubo_agente"):
            grupos[e.agente_id].append(e)
    filas = []
    for ag, es in sorted(grupos.items()):
        cargas = [_s(e, "carga_emocional_agente") or 0 for e in es]
        hostiles = sum(1 for x in cargas if x >= 25)
        filas.append({
            "agente_id": ag, "n": len(es),
            "puntaje_promedio": round(statistics.fmean(e.puntaje for e in es), 1),
            "con_error_critico": sum(1 for e in es if e.errores_criticos),
            "carga_emocional_promedio": round(statistics.fmean(cargas), 1),
            "interacciones_hostiles": hostiles,
            "alerta_psicosocial": len(es) >= 4 and hostiles / len(es) >= 0.25,
        })
    return filas


def por_tema(evs: list[Evaluacion]) -> list[dict]:
    grupos: dict[str, list[Evaluacion]] = defaultdict(list)
    for e in evs:
        for t in _s(e, "temas") or ["sin_tema"]:
            grupos[t].append(e)
    filas = []
    for t, es in grupos.items():
        at = [e for e in es if e.tipo != "ventas"]
        res = sum(1 for e in at if (cr := _criterio(e, "R1")) and cr.cumple)
        filas.append({
            "tema": t, "n": len(es),
            "resolucion": (res / len(at)) if at else None,
            "frustracion_promedio": round(statistics.fmean(_s(e, "frustracion_max") or 0 for e in es), 1),
        })
    return sorted(filas, key=lambda f: -f["n"])


def por_modalidad(evs: list[Evaluacion]) -> list[dict]:
    def modalidad(e: Evaluacion) -> str:
        b, a = _s(e, "hubo_bot"), _s(e, "hubo_agente")
        return "bot → persona" if b and a else "solo bot" if b else "solo persona"
    grupos: dict[str, list[Evaluacion]] = defaultdict(list)
    for e in evs:
        grupos[modalidad(e)].append(e)
    return [
        {"modalidad": m, "n": len(es), "puntaje_promedio": round(statistics.fmean(e.puntaje for e in es), 1),
         "con_error_critico": sum(1 for e in es if e.errores_criticos)}
        for m, es in sorted(grupos.items())
    ]


def por_criterio(evs: list[Evaluacion]) -> list[dict]:
    """Tasa de cumplimiento de cada criterio: dónde está el problema de la operación."""
    acum: dict[str, dict] = {}
    for e in evs:
        for c in e.criterios:
            if not c.aplica:
                continue
            a = acum.setdefault(c.id, {"id": c.id, "nombre": c.nombre, "dimension": c.dimension, "critico": c.critico, "aplica": 0, "cumple": 0})
            a["aplica"] += 1
            a["cumple"] += 1 if c.cumple else 0
    filas = list(acum.values())
    for f in filas:
        f["tasa"] = f["cumple"] / f["aplica"] if f["aplica"] else None
    return sorted(filas, key=lambda f: (f["tasa"] if f["tasa"] is not None else 1))


def comparar(antes: list[Evaluacion], despues: list[Evaluacion], alfa: float = 0.05) -> list[dict]:
    """¿Mejoró de verdad? Compara cada indicador entre dos periodos con IC 95 % y p-valor."""
    a, d = calcular(antes), calcular(despues)
    filas = []
    for ia, idd in zip(a["indicadores"], d["indicadores"]):
        fila = {"id": ia.id, "nombre": ia.nombre, "sentido": ia.sentido, "unidad": ia.unidad,
                "antes": ia.valor, "n_antes": ia.n, "despues": idd.valor, "n_despues": idd.n}
        if ia.unidad == "%":
            r = diferencia_proporciones(ia.x, ia.n, idd.x, idd.n)
        elif ia.id == "I04":
            r = {"diferencia": (idd.valor - ia.valor) if ia.valor is not None and idd.valor is not None else None, "ic95": None, "p_valor": None}
        else:
            r = diferencia_medias(ia.muestras, idd.muestras)
        fila.update(r)
        dif, p = r.get("diferencia"), r.get("p_valor")
        if dif is None or p is None:
            veredicto = "sin datos suficientes"
        elif p < alfa:
            mejor = dif > 0 if ia.sentido == "mayor" else dif < 0
            veredicto = "mejora significativa" if mejor else "empeora significativamente"
        else:
            veredicto = "sin cambio concluyente"
        if min(ia.n, idd.n) < 30 and veredicto != "sin datos suficientes":
            veredicto += " (muestra pequeña)"
        fila["veredicto"] = veredicto
        filas.append(fila)
    return filas
