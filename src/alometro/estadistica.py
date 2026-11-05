"""Estadística mínima, sin dependencias, para decidir si una mejora es real.

* Intervalo de Wilson para proporciones (se comporta bien con n pequeño).
* Diferencia de proporciones con IC de Newcombe (método 10) y prueba z.
* Kappa de Cohen para medir el acuerdo entre Alómetro y evaluadores humanos.
* Correlación de Spearman (p. ej. puntaje de Alómetro vs. CSAT).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Hashable, Sequence

Z95 = 1.959963984540054


def wilson(exitos: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = exitos / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centro - margen), min(1.0, centro + margen))


def diferencia_proporciones(x1: int, n1: int, x2: int, n2: int) -> dict:
    """Compara p2 - p1 (después - antes). Devuelve diferencia, IC 95 % (Newcombe) y p-valor (z bilateral)."""
    if n1 == 0 or n2 == 0:
        return {"diferencia": None, "ic95": None, "p_valor": None}
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1)
    l2, u2 = wilson(x2, n2)
    d = p2 - p1
    inf = d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    sup = d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    pc = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pc * (1 - pc) * (1 / n1 + 1 / n2))
    p_valor = 1.0 if se == 0 else math.erfc(abs(d / se) / math.sqrt(2))
    return {"diferencia": d, "ic95": (inf, sup), "p_valor": p_valor}


def diferencia_medias(a: Sequence[float], b: Sequence[float]) -> dict:
    """Diferencia de medias (b - a) con IC 95 % de Welch (aproximación normal)."""
    if len(a) < 2 or len(b) < 2:
        return {"diferencia": None, "ic95": None, "p_valor": None}
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    d = mb - ma
    if se == 0:
        return {"diferencia": d, "ic95": (d, d), "p_valor": 1.0 if d == 0 else 0.0}
    return {"diferencia": d, "ic95": (d - Z95 * se, d + Z95 * se), "p_valor": math.erfc(abs(d / se) / math.sqrt(2))}


def kappa_cohen(a: Sequence[Hashable], b: Sequence[Hashable]) -> float | None:
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1:
        return None  # sin variación en las etiquetas: kappa no está definido
    return (po - pe) / (1 - pe)


def interpretar_kappa(k: float | None) -> str:
    if k is None:
        return "sin datos"
    for limite, txt in ((0.8, "casi perfecto"), (0.6, "sustancial"), (0.4, "moderado"), (0.2, "aceptable"), (0.0, "leve")):
        if k > limite:
            return txt
    return "pobre"


def _rangos(x: Sequence[float]) -> list[float]:
    orden = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and x[orden[j + 1]] == x[orden[i]]:
            j += 1
        prom = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[orden[k]] = prom
        i = j + 1
    return r


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) != len(y) or len(x) < 3:
        return None
    rx, ry = _rangos(x), _rangos(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return None if den == 0 else num / den


def tamano_muestra(p: float = 0.5, margen: float = 0.05, z: float = Z95) -> int:
    """Interacciones a evaluar para estimar una proporción con el margen dado."""
    return math.ceil(z * z * p * (1 - p) / (margen * margen))
