"""Cada escenario sintético tiene un resultado esperado conocido (prueba de regresión)."""

import random
from datetime import datetime

import pytest

from alometro.calendario import HORA_COLOMBIA
from alometro.motor import Politica, evaluar
from alometro.sintetico import ESCENARIOS, _conv

V = {"ag": "Laura", "cli": "María", "ced": "1.023.456.789", "cel": "300 123 4567", "rad": "43-1234567890"}
HABIL = datetime(2026, 10, 14, 10, 0, tzinfo=HORA_COLOMBIA)
DOMINGO_NOCHE = datetime(2026, 10, 18, 20, 0, tzinfo=HORA_COLOMBIA)

ESPERADO = {  # escenario: (errores críticos exactos, puntaje base mínimo, puntaje base máximo)
    "servicio_ejemplar": (set(), 95, 100),
    "bot_bucle_sin_humano": ({"R3", "B2C", "B5"}, 0, 50),
    "bot_a_persona_sin_contexto": (set(), 40, 80),
    "bot_a_persona_con_contexto": (set(), 95, 100),
    "bot_resuelve": (set(), 85, 100),
    "bot_pide_humano_atendido": (set(), 95, 100),
    "queja_radicada": (set(), 95, 100),
    "agente_evasivo": ({"R3"}, 0, 45),
    "cancelacion_con_retencion": ({"R3", "L7"}, 0, 70),
    "cancelacion_correcta": (set(), 95, 100),
    "venta_correcta": (set(), 95, 100),
    "venta_agresiva": ({"L1", "L2", "L3"}, 0, 70),
    "cobranza_respetuosa": (set(), 95, 100),
    "cobranza_coercitiva": ({"L1", "L8"}, 0, 50),
    "cliente_hostil_desescalada": (set(), 90, 100),
    "pide_otp": ({"L9"}, 0, 90),
    "soporte_transferencias": (set(), 0, 50),
}


def _evaluar(nombre, politica=None):
    tipo, canal, sector, d, turnos = ESCENARIOS[nombre](random.Random(1), V)
    fecha = DOMINGO_NOCHE if nombre in ("venta_agresiva", "cobranza_coercitiva") else HABIL
    return evaluar(_conv(nombre, tipo, canal, sector, d, fecha, "c1", "A01", turnos, nombre), politica)


def test_todos_los_escenarios_tienen_expectativa():
    assert set(ESPERADO) == set(ESCENARIOS)


@pytest.mark.parametrize("nombre", sorted(ESPERADO))
def test_escenario(nombre):
    criticos, minimo, maximo = ESPERADO[nombre]
    e = _evaluar(nombre)
    assert {x["criterio"] for x in e.errores_criticos} == criticos
    assert minimo <= e.puntaje_base <= maximo
    if criticos:
        assert e.puntaje == 0 and e.nivel == "Crítico"


def test_politica_sin_anular():
    e = _evaluar("pide_otp", Politica(anular_por_critico=False))
    assert e.puntaje == e.puntaje_base > 0


def test_politica_desactivar_y_pesos():
    e = _evaluar("bot_a_persona_sin_contexto", Politica(desactivar={"E2", "B4"}))
    assert all(c.id not in {"E2", "B4"} for c in e.criterios)


def test_evidencias_anonimizadas():
    e = _evaluar("bot_a_persona_sin_contexto")
    textos = " ".join(ev.cita for c in e.criterios for ev in c.evidencias)
    assert "1.023.456.789" not in textos


def test_cada_falla_trae_recomendacion_y_evidencia_si_aplica():
    e = _evaluar("bot_bucle_sin_humano")
    for c in e.criterios:
        if c.aplica and c.cumple is False:
            assert c.recomendacion


def test_criterios_tienen_fundamento():
    from alometro.rubrica import CRITERIOS
    ids = [c.id for c in CRITERIOS]
    assert len(ids) == len(set(ids))
    for c in CRITERIOS:
        assert c.fundamento and c.recomendacion
        assert (c.peso == 0) == (c.critico is not None)
