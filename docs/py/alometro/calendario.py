"""Calendario colombiano y franjas de contacto de la Ley 2300 de 2023.

Festivos según la Ley 51 de 1983 («Ley Emiliani»): algunos se trasladan al
lunes siguiente y otros dependen de la Pascua. Se calcula sin dependencias.

Ley 2300 de 2023 (art. 3): la gestión de cobranza (y, por remisión, el envío de
publicidad y ofertas comerciales) solo puede contactar al consumidor de lunes a
viernes de 7:00 a. m. a 7:00 p. m. y los sábados de 8:00 a. m. a 3:00 p. m.; nunca
domingos ni festivos. Tras un contacto directo, no puede contactarse más de una
vez el mismo día ni por varios canales en la misma semana.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache

HORA_COLOMBIA = timezone(timedelta(hours=-5), "COT")  # Colombia no usa horario de verano


def _pascua(anio: int) -> date:
    """Domingo de Pascua (algoritmo de Meeus/Jones/Butcher, calendario gregoriano)."""
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def _siguiente_lunes(d: date) -> date:
    return d + timedelta(days=(7 - d.weekday()) % 7)


@lru_cache(maxsize=64)
def festivos(anio: int) -> dict[date, str]:
    p = _pascua(anio)
    fijos = {
        date(anio, 1, 1): "Año Nuevo",
        date(anio, 5, 1): "Día del Trabajo",
        date(anio, 7, 20): "Independencia",
        date(anio, 8, 7): "Batalla de Boyacá",
        date(anio, 12, 8): "Inmaculada Concepción",
        date(anio, 12, 25): "Navidad",
    }
    emiliani = {
        date(anio, 1, 6): "Reyes Magos",
        date(anio, 3, 19): "San José",
        date(anio, 6, 29): "San Pedro y San Pablo",
        date(anio, 8, 15): "Asunción de la Virgen",
        date(anio, 10, 12): "Día de la Raza",
        date(anio, 11, 1): "Todos los Santos",
        date(anio, 11, 11): "Independencia de Cartagena",
    }
    res = dict(fijos)
    for d, n in emiliani.items():
        res[_siguiente_lunes(d)] = n
    res[p - timedelta(days=3)] = "Jueves Santo"
    res[p - timedelta(days=2)] = "Viernes Santo"
    res[p + timedelta(days=43)] = "Ascensión del Señor"
    res[p + timedelta(days=64)] = "Corpus Christi"
    res[p + timedelta(days=71)] = "Sagrado Corazón"
    return res


def es_festivo(d: date) -> str | None:
    return festivos(d.year).get(d)


def a_hora_colombia(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=HORA_COLOMBIA)  # se asume hora local colombiana
    return dt.astimezone(HORA_COLOMBIA)


def ventana_ley_2300(dt: datetime) -> tuple[bool, str]:
    """¿Está `dt` dentro de la franja permitida? Devuelve (permitido, motivo)."""
    local = a_hora_colombia(dt)
    d, h = local.date(), local.time()
    festivo = es_festivo(d)
    if festivo:
        return False, f"{d.isoformat()} es festivo ({festivo})"
    dia = d.weekday()  # 0 = lunes
    if dia == 6:
        return False, f"{d.isoformat()} es domingo"
    if dia == 5:
        ok = time(8, 0) <= h <= time(15, 0)
        return ok, ("sábado dentro de 8:00-15:00" if ok else f"sábado a las {h.strftime('%H:%M')} (permitido 8:00-15:00)")
    ok = time(7, 0) <= h <= time(19, 0)
    return ok, ("día hábil dentro de 7:00-19:00" if ok else f"día hábil a las {h.strftime('%H:%M')} (permitido 7:00-19:00)")
