from alometro.calibracion import calibrar, leer_etiquetas
from alometro.cli import main
from alometro.indicadores import calcular
from alometro.informe import generar_html
from alometro.motor import evaluar_lote
from conftest import conv


def test_demo_evaluar_comparar(tmp_path, capsys):
    d = tmp_path / "demo"
    assert main(["demo", "--carpeta", str(d), "-n", "60"]) == 0
    assert main(["evaluar", str(d / "antes.jsonl"), "-o", str(tmp_path / "i.html"), "--json", str(tmp_path / "r.json"),
                 "--csv", str(tmp_path / "r.csv")]) == 0
    assert (tmp_path / "i.html").read_text(encoding="utf-8").startswith("<!doctype html>")
    assert "conversacion_id" in (tmp_path / "r.csv").read_text(encoding="utf-8")
    assert main(["comparar", str(d / "antes.jsonl"), str(d / "despues.jsonl")]) == 0
    assert "Veredicto" in capsys.readouterr().out
    assert main(["criterios"]) == 0


def test_informe_escapa_html():
    evs = evaluar_lote([conv([("cliente", "<script>alert(1)</script> no sirve para nada"), ("agente", "Eso no es conmigo")])])
    h = generar_html(evs, calcular(evs))
    assert "<script>alert" not in h


def test_calibracion_kappa(tmp_path):
    evs = evaluar_lote([
        conv([("cliente", "hola"), ("agente", "Listo, ya quedó solucionado")], id="a"),
        conv([("cliente", "hola"), ("agente", "Eso no es conmigo, llame más tarde")], id="b"),
    ])
    et = leer_etiquetas("conversacion_id,criterio,cumple\na,R1,1\nb,R1,0\n")
    res = calibrar(evs, et)
    fila = res["criterios"][0]
    assert fila["criterio"] == "R1" and fila["acuerdo"] == 1.0 and fila["kappa"] == 1.0
    ancho = leer_etiquetas("conversacion_id,R1,T4\na,si,si\nb,no,no\n")
    assert ancho[("b", "T4")] is False
