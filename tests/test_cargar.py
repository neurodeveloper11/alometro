import json

import pytest

from alometro.cargar import a_jsonl, desde_csv, desde_jsonl, desde_txt
from alometro.modelos import Conversacion, Turno


def test_jsonl_ida_y_vuelta():
    d = {"id": "a", "tipo": "ventas", "canal": "voz", "inicio": "2026-10-13T10:00:00-05:00", "cliente_id": "c1",
         "turnos": [{"rol": "agent", "texto": "Hola"}, {"rol": "customer", "texto": "Hola"}]}
    c = desde_jsonl(json.dumps(d))[0]
    assert c.direccion == "saliente"  # ventas -> saliente por defecto
    assert [t.rol for t in c.turnos] == ["agente", "cliente"]
    c2 = desde_jsonl(a_jsonl([c]))[0]
    assert c2.inicio == c.inicio and c2.turnos[0].texto == "Hola"


def test_csv_agrupa_por_conversacion():
    texto = "conversacion_id,rol,texto,tipo\nx,bot,Hola,servicio\nx,cliente,asesor,servicio\ny,agente,Buenas,soporte\n"
    convs = desde_csv(texto)
    assert len(convs) == 2 and len(convs[0].turnos) == 2 and convs[1].tipo == "soporte"


def test_txt_con_metadatos_y_marcas_de_tiempo():
    texto = "# tipo: cancelacion | canal: voz | sector: telecom\n[00:05] Agente: Buenas tardes\n[00:09] Cliente: Quiero cancelar\ncontinúa aquí\n"
    c = desde_txt(texto)
    assert c.tipo == "cancelacion" and c.sector == "telecom"
    assert c.turnos[0].t == 5.0 and c.turnos[1].texto.endswith("continúa aquí")


def test_rol_invalido():
    with pytest.raises(ValueError):
        Turno(rol="marciano", texto="x")


def test_tipo_invalido():
    with pytest.raises(ValueError):
        Conversacion(id="x", turnos=[], tipo="desconocido")
