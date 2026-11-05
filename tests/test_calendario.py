from datetime import date, datetime

from alometro.calendario import HORA_COLOMBIA, _pascua, festivos, ventana_ley_2300


def test_pascua_conocidas():
    assert _pascua(2024) == date(2024, 3, 31)
    assert _pascua(2025) == date(2025, 4, 20)
    assert _pascua(2026) == date(2026, 4, 5)


def test_festivos_colombia_2026():
    esperados = {
        date(2026, 1, 1), date(2026, 1, 12), date(2026, 3, 23), date(2026, 4, 2), date(2026, 4, 3),
        date(2026, 5, 1), date(2026, 5, 18), date(2026, 6, 8), date(2026, 6, 15), date(2026, 6, 29),
        date(2026, 7, 20), date(2026, 8, 7), date(2026, 8, 17), date(2026, 10, 12), date(2026, 11, 2),
        date(2026, 11, 16), date(2026, 12, 8), date(2026, 12, 25),
    }
    assert set(festivos(2026)) == esperados


def _v(y, m, d, h, mi=0):
    return ventana_ley_2300(datetime(y, m, d, h, mi, tzinfo=HORA_COLOMBIA))


def test_ventana_dia_habil():
    assert _v(2026, 10, 13, 7, 0)[0]
    assert _v(2026, 10, 13, 19, 0)[0]
    assert not _v(2026, 10, 13, 19, 1)[0]
    assert not _v(2026, 10, 13, 6, 59)[0]


def test_ventana_sabado_domingo_festivo():
    assert _v(2026, 10, 17, 14, 59)[0]
    assert not _v(2026, 10, 17, 15, 30)[0]
    assert not _v(2026, 10, 18, 10)[0]          # domingo
    ok, motivo = _v(2026, 10, 12, 10)            # Día de la Raza (lunes festivo)
    assert not ok and "festivo" in motivo


def test_ventana_convierte_zona_horaria():
    from datetime import timezone
    # 00:30 UTC del martes = 19:30 del lunes en Colombia -> fuera de horario
    assert not ventana_ley_2300(datetime(2026, 10, 14, 0, 30, tzinfo=timezone.utc))[0]
