"""Plan de coaching por agente: qué entrenar primero, con ejemplos reales.

Para cada agente:

* **Prioridades** (máx. 3): criterios donde falla con más frecuencia que el equipo.
  Primero los errores críticos, luego por «impacto» = tasa de falla × peso.
  Si todo el equipo falla igual, el problema es del proceso (guion, sistema,
  política) y no del agente: se marca como «problema de proceso».
* **Ejemplo**: la conversación y la cita que muestran la falla, para la sesión 1:1.
* **Fortalezas**: criterios que cumple siempre (para reconocer, no solo corregir).
"""

from __future__ import annotations

from collections import defaultdict

from .modelos import Evaluacion
from .rubrica import CRITERIOS_POR_ID

MIN_CASOS = 3  # aplicaciones mínimas de un criterio para opinar sobre él


def _tasas(evs: list[Evaluacion]) -> dict[str, dict]:
    t: dict[str, dict] = defaultdict(lambda: {"aplica": 0, "falla": 0, "ejemplo": None})
    for e in evs:
        for c in e.criterios:
            if not c.aplica:
                continue
            x = t[c.id]
            x["aplica"] += 1
            if c.cumple is False:
                x["falla"] += 1
                if x["ejemplo"] is None:
                    ev = c.evidencias[0] if c.evidencias else None
                    x["ejemplo"] = {"conversacion_id": e.conversacion_id, "detalle": c.detalle,
                                    "turno": ev.turno if ev else None, "cita": ev.cita if ev else ""}
    return t


def plan_coaching(evs: list[Evaluacion], max_prioridades: int = 3) -> list[dict]:
    con_agente = [e for e in evs if e.agente_id and e.senales.get("hubo_agente")]
    equipo = _tasas(con_agente)
    por_agente: dict[str, list[Evaluacion]] = defaultdict(list)
    for e in con_agente:
        por_agente[e.agente_id].append(e)
    planes = []
    for ag, es in sorted(por_agente.items()):
        propias = _tasas(es)
        candidatos = []
        for cid, x in propias.items():
            if CRITERIOS_POR_ID[cid].dimension == "bot":
                continue  # el comportamiento del bot no es responsabilidad del agente
            if x["aplica"] < MIN_CASOS and not (CRITERIOS_POR_ID[cid].critico and x["falla"]):
                continue
            if not x["falla"]:
                continue
            cr = CRITERIOS_POR_ID[cid]
            tasa = x["falla"] / x["aplica"]
            eq = equipo[cid]
            tasa_eq = eq["falla"] / eq["aplica"] if eq["aplica"] else 0.0
            otros_aplica, otros_falla = eq["aplica"] - x["aplica"], eq["falla"] - x["falla"]
            tasa_otros = otros_falla / otros_aplica if otros_aplica >= MIN_CASOS else None
            # Es del proceso si los DEMÁS agentes también fallan (y con datos suficientes para saberlo).
            de_proceso = tasa_otros is not None and tasa_otros >= 0.5 and tasa_otros >= 0.8 * tasa
            impacto = tasa * (cr.peso or 25)  # un crítico pesa como el criterio más importante
            candidatos.append({
                "criterio": cid, "nombre": cr.nombre, "critico": cr.critico, "fallas": x["falla"], "aplica": x["aplica"],
                "tasa": tasa, "tasa_equipo": tasa_eq,
                "origen": "proceso" if de_proceso else "agente",
                "recomendacion": cr.recomendacion, "ejemplo": x["ejemplo"], "_orden": (cr.critico is None, -impacto),
            })
        candidatos.sort(key=lambda c: c["_orden"])
        prioridades = [{k: v for k, v in c.items() if k != "_orden"} for c in candidatos[:max_prioridades]]
        fortalezas = sorted(
            (cid for cid, x in propias.items() if x["aplica"] >= MIN_CASOS and x["falla"] == 0 and CRITERIOS_POR_ID[cid].peso > 0
             and CRITERIOS_POR_ID[cid].dimension != "bot"),
            key=lambda cid: -CRITERIOS_POR_ID[cid].peso)[:3]
        planes.append({
            "agente_id": ag, "interacciones": len(es),
            "puntaje_promedio": round(sum(e.puntaje for e in es) / len(es), 1),
            "prioridades": prioridades,
            "fortalezas": [{"criterio": c, "nombre": CRITERIOS_POR_ID[c].nombre} for c in fortalezas],
        })
    return sorted(planes, key=lambda p: p["puntaje_promedio"])


def coaching_csv(planes: list[dict]) -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["agente_id", "interacciones", "puntaje_promedio", "prioridad", "criterio", "nombre", "fallas", "aplica",
                "tasa_agente", "tasa_equipo", "origen", "recomendacion", "ejemplo_conversacion", "ejemplo_cita", "fortalezas"])
    for p in planes:
        fort = "; ".join(f"{f['criterio']} {f['nombre']}" for f in p["fortalezas"])
        if not p["prioridades"]:
            w.writerow([p["agente_id"], p["interacciones"], p["puntaje_promedio"], "", "", "Sin prioridades", "", "", "", "", "", "", "", "", fort])
        for i, c in enumerate(p["prioridades"], 1):
            ej = c["ejemplo"] or {}
            w.writerow([p["agente_id"], p["interacciones"], p["puntaje_promedio"], i, c["criterio"], c["nombre"], c["fallas"], c["aplica"],
                        f"{c['tasa']:.2f}", f"{c['tasa_equipo']:.2f}", c["origen"], c["recomendacion"],
                        ej.get("conversacion_id", ""), ej.get("cita") or ej.get("detalle", ""), fort])
    return buf.getvalue()
