from alometro.cli import main
from alometro.coaching import coaching_csv, plan_coaching
from alometro.modelos import Conversacion, Turno
from alometro.motor import evaluar_lote


def _conv(i, agente, malo):
    if malo:
        t = [("cliente", "Llevo tres días sin internet, es el colmo"), ("agente", "Eso no es conmigo, llame más tarde")]
    else:
        t = [("agente", "Buenas tardes, le habla Ana de ConectaYa. ¿En qué le puedo ayudar?"),
             ("cliente", "No tengo internet, estoy molesta"), ("agente", "Entiendo su molestia, yo me encargo. Listo, ya quedó restablecido el servicio."),
             ("cliente", "Perfecto, gracias"), ("agente", "Le confirmo: servicio restablecido. ¿Algo más en lo que le pueda ayudar? Que tenga buen día.")]
    return Conversacion(id=f"c{i}", agente_id=agente, canal="chat", turnos=[Turno(r, x) for r, x in t])


def test_prioriza_lo_que_falla_y_reconoce_fortalezas():
    evs = evaluar_lote([_conv(i, "MALO", True) for i in range(4)] + [_conv(10 + i, "BUENO", False) for i in range(4)])
    planes = {p["agente_id"]: p for p in plan_coaching(evs)}
    malo, bueno = planes["MALO"], planes["BUENO"]
    assert malo["prioridades"][0]["critico"] == "cliente"  # los críticos primero (R3 callejón sin salida)
    assert all(p["origen"] == "agente" for p in malo["prioridades"])  # el otro agente no falla: es del agente
    assert malo["prioridades"][0]["ejemplo"]["cita"]
    assert not bueno["prioridades"] and any(f["criterio"] == "R1" for f in bueno["fortalezas"])
    assert list(planes) == ["MALO", "BUENO"] or plan_coaching(evs)[0]["agente_id"] == "MALO"  # peor puntaje primero


def test_problema_de_proceso_cuando_todo_el_equipo_falla():
    evs = evaluar_lote([_conv(i, f"A{i % 2}", True) for i in range(8)])
    assert all(c["origen"] == "proceso" for p in plan_coaching(evs) for c in p["prioridades"])


def test_csv_y_cli(tmp_path):
    evs = evaluar_lote([_conv(i, "A1", True) for i in range(3)])
    assert "agente_id" in coaching_csv(plan_coaching(evs))
    d = tmp_path / "demo"
    main(["demo", "--carpeta", str(d), "-n", "80"])
    assert main(["evaluar", str(d / "antes.jsonl"), "-o", str(tmp_path / "i.html"), "--coaching", str(tmp_path / "c.csv")]) == 0
    assert "recomendacion" in (tmp_path / "c.csv").read_text(encoding="utf-8")
    assert "Plan de coaching por agente" in (tmp_path / "i.html").read_text(encoding="utf-8")
