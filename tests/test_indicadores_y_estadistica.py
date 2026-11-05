import math
from datetime import datetime

from alometro.calendario import HORA_COLOMBIA
from alometro.estadistica import diferencia_proporciones, kappa_cohen, spearman, tamano_muestra, wilson
from alometro.indicadores import calcular, comparar, frecuencia_ley_2300, recontactos
from alometro.motor import evaluar_lote
from alometro.sintetico import generar
from conftest import conv


def test_wilson_valores_conocidos():
    lo, hi = wilson(50, 100)
    assert math.isclose(lo, 0.4038, abs_tol=1e-3) and math.isclose(hi, 0.5962, abs_tol=1e-3)
    assert wilson(0, 0) == (0.0, 1.0)


def test_diferencia_proporciones():
    r = diferencia_proporciones(40, 100, 60, 100)
    assert math.isclose(r["diferencia"], 0.2)
    assert r["p_valor"] < 0.01 and r["ic95"][0] > 0


def test_kappa_y_spearman():
    assert kappa_cohen([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0
    assert math.isclose(kappa_cohen([1, 0, 1, 0], [1, 1, 0, 0]), 0.0)
    assert math.isclose(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
    assert tamano_muestra() == 385


def _ev(cid, cliente, dia, tipo="servicio", canal="voz", direccion=None, hora=10):
    c = conv([("cliente", "hola"), ("agente", "Listo, ya quedó solucionado")], id=cid, tipo=tipo, canal=canal,
             cliente_id=cliente, direccion=direccion, inicio=datetime(2026, 10, dia, hora, 0, tzinfo=HORA_COLOMBIA))
    return evaluar_lote([c])[0]


def test_recontacto_y_censura():
    evs = [_ev("a", "c1", 1), _ev("b", "c1", 5), _ev("c", "c2", 2), _ev("d", "c3", 28)]
    r = recontactos(evs, 7)
    assert r["a"] is True        # volvió a los 4 días
    assert r["c"] is False       # observable 7 días y no volvió
    assert r["d"] is None        # sin 7 días de observación al final del periodo


def test_frecuencia_ley_2300():
    evs = [_ev("a", "c1", 13, tipo="cobranza", hora=9), _ev("b", "c1", 13, tipo="cobranza", hora=15, canal="whatsapp")]
    reglas = {a["regla"] for a in frecuencia_ley_2300(evs)}
    assert reglas == {"más de un contacto el mismo día", "varios canales en la misma semana"}


def test_calcular_y_comparar_demo():
    antes = evaluar_lote(generar(160, "antes", semilla=3))
    despues = evaluar_lote(generar(160, "despues", semilla=3))
    res = calcular(antes)
    ids = {i.id for i in res["indicadores"]}
    assert {"I01", "I02", "I03", "I05", "I06", "I12", "I16"} <= ids
    assert res["contencion"]["contencion_real"] <= res["contencion"]["contencion_bruta"]
    assert res["ley_2300_frecuencia"]
    filas = {f["id"]: f for f in comparar(antes, despues)}
    assert filas["I16"]["veredicto"].startswith("mejora significativa")
    assert filas["I05"]["veredicto"].startswith("mejora significativa")
