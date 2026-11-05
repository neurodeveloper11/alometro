"""Utilidades de texto para español de Colombia.

La normalización quita tildes y pasa a minúsculas para que «está», «esta» y
«ESTÁ» coincidan con los mismos patrones. Los índices de las evidencias siempre
se toman del texto original.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from re import Pattern

_ESPACIOS = re.compile(r"\s+")
_PALABRA = re.compile(r"[a-z0-9ñ]+")


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes ni diéresis, espacios colapsados. La ñ pasa a n."""
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return _ESPACIOS.sub(" ", t.lower()).strip()


def palabras(texto_norm: str) -> list[str]:
    return _PALABRA.findall(texto_norm)


def jaccard(a: str, b: str) -> float:
    """Similitud de Jaccard entre los conjuntos de palabras de dos textos normalizados."""
    sa, sb = set(palabras(a)), set(palabras(b))
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def compilar(patrones: Iterable[str]) -> list[Pattern[str]]:
    return [re.compile(p) for p in patrones]


def buscar(patrones: list[Pattern[str]], texto_norm: str) -> str | None:
    """Devuelve el primer fragmento que coincide, o None."""
    for p in patrones:
        m = p.search(texto_norm)
        if m:
            return m.group(0)
    return None


def contar(patrones: list[Pattern[str]], texto_norm: str) -> int:
    return sum(len(p.findall(texto_norm)) for p in patrones)


def recortar(texto: str, n: int = 160) -> str:
    texto = _ESPACIOS.sub(" ", texto).strip()
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def proporcion_mayusculas(texto: str) -> float:
    letras = [c for c in texto if c.isalpha()]
    if len(letras) < 8:
        return 0.0
    return sum(1 for c in letras if c.isupper()) / len(letras)


def luhn_valido(digitos: str) -> bool:
    d = [int(c) for c in digitos if c.isdigit()]
    if len(d) < 13 or len(d) > 19:
        return False
    total = 0
    for i, x in enumerate(reversed(d)):
        if i % 2 == 1:
            x *= 2
            if x > 9:
                x -= 9
        total += x
    return total % 10 == 0
