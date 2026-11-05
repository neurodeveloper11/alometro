"""Calibración: ¿Alómetro mide lo mismo que un buen analista de calidad?

Antes de usar los resultados para decisiones (bonos, coaching, contratos con un
BPO), compare Alómetro con evaluaciones humanas de una muestra:

1. Dos analistas califican la misma muestra (≥ 50 interacciones) con los mismos
   criterios. Su acuerdo (kappa) es el techo alcanzable.
2. Alómetro califica la misma muestra. Se calcula kappa Alómetro-humano por criterio.
3. Criterio con kappa < 0,6: se revisan sus patrones (`lexicos.py`) o se excluye
   de la nota hasta mejorarlo.

Formato de etiquetas (CSV largo): ``conversacion_id,criterio,cumple`` con cumple
en {1, 0, si, no, na}. También se acepta formato ancho: una columna por criterio.
"""

from __future__ import annotations

import csv
import io
from collections import defaultdict

from .estadistica import interpretar_kappa, kappa_cohen, spearman
from .modelos import Evaluacion

_SI = {"1", "si", "sí", "s", "true", "cumple", "x", "yes", "y"}
_NO = {"0", "no", "n", "false", "falla", "no cumple"}


def _valor(v: str) -> bool | None:
    v = (v or "").strip().lower()
    if v in _SI:
        return True
    if v in _NO:
        return False
    return None


def leer_etiquetas(texto: str) -> dict[tuple[str, str], bool]:
    filas = list(csv.DictReader(io.StringIO(texto)))
    if not filas:
        return {}
    res: dict[tuple[str, str], bool] = {}
    cols = set(filas[0])
    if {"conversacion_id", "criterio", "cumple"} <= cols:
        for f in filas:
            v = _valor(f["cumple"])
            if v is not None:
                res[(f["conversacion_id"], f["criterio"].strip().upper())] = v
    else:
        for f in filas:
            cid = f.get("conversacion_id") or f.get("id")
            for k, val in f.items():
                if k in ("conversacion_id", "id"):
                    continue
                v = _valor(val)
                if v is not None:
                    res[(cid, k.strip().upper())] = v
    return res


def calibrar(evs: list[Evaluacion], etiquetas: dict[tuple[str, str], bool], csat: dict[str, float] | None = None) -> dict:
    por_crit: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    mapa = {e.conversacion_id: e for e in evs}
    for (cid, crit), humano in etiquetas.items():
        e = mapa.get(cid)
        if not e:
            continue
        r = next((c for c in e.criterios if c.id == crit), None)
        if r is None or not r.aplica:
            continue
        por_crit[crit].append((bool(r.cumple), humano))
    filas = []
    for crit, pares in sorted(por_crit.items()):
        a = [x for x, _ in pares]
        h = [y for _, y in pares]
        k = kappa_cohen(a, h)
        # "Falla" como clase positiva: ¿Alómetro encuentra las fallas que ve el humano?
        vp = sum(1 for x, y in pares if not x and not y)
        fp = sum(1 for x, y in pares if not x and y)
        fn = sum(1 for x, y in pares if x and not y)
        filas.append({
            "criterio": crit, "n": len(pares),
            "acuerdo": sum(1 for x, y in pares if x == y) / len(pares),
            "kappa": k, "interpretacion": interpretar_kappa(k),
            "precision_fallas": vp / (vp + fp) if vp + fp else None,
            "sensibilidad_fallas": vp / (vp + fn) if vp + fn else None,
            "apto": k is not None and k >= 0.6 and len(pares) >= 20,
        })
    res = {"criterios": filas}
    if csat:
        pares = [(e.puntaje, csat[e.conversacion_id]) for e in evs if e.conversacion_id in csat]
        rho = spearman([p for p, _ in pares], [c for _, c in pares]) if len(pares) >= 3 else None
        res["validez_csat"] = {"n": len(pares), "spearman": rho}
    return res
