"""Construye la web de presentación (docs/) con datos calculados por el motor real.

    python scripts/construir_web.py [--artifact RUTA]

* docs/index.html      página completa para GitHub Pages (con demo en vivo vía Pyodide)
* docs/py/alometro/    copia del paquete para ejecutarlo en el navegador
* --artifact RUTA      versión fragmento (sin <html>/<head>) para publicar como artifact
"""
import json
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from alometro import __version__  # noqa: E402
from alometro.calendario import HORA_COLOMBIA  # noqa: E402
from alometro.indicadores import INDICADORES, calcular, comparar  # noqa: E402
from alometro.motor import evaluar, evaluar_lote  # noqa: E402
from alometro.rubrica import CRITERIOS, DIMENSIONES  # noqa: E402
from alometro.sintetico import ESCENARIOS, _conv, generar  # noqa: E402

EJEMPLOS = [
    ("bot_bucle_sin_humano", "El bot que no deja salir", "WhatsApp · servicio · telecomunicaciones", datetime(2026, 10, 14, 19, 12)),
    ("bot_a_persona_sin_contexto", "Traspaso que pide la cédula otra vez", "Chat · fraude · banca", datetime(2026, 10, 14, 10, 40)),
    ("bot_a_persona_con_contexto", "Traspaso bien hecho", "Chat · fraude · banca", datetime(2026, 10, 14, 10, 40)),
    ("cancelacion_con_retencion", "Cancelación con trabas", "Voz · cancelación · telecomunicaciones", datetime(2026, 10, 15, 16, 5)),
    ("venta_agresiva", "Venta insistente un domingo", "Voz saliente · ventas · telecomunicaciones", datetime(2026, 10, 18, 20, 10)),
    ("cliente_hostil_desescalada", "Cliente furioso que termina calmado", "Voz · soporte · telecomunicaciones", datetime(2026, 10, 13, 20, 30)),
]
V = {"ag": "Laura", "cli": "María", "ced": "1.023.456.789", "cel": "300 123 4567", "rad": "43-1290348812"}


def ejemplo(clave, titulo, contexto, fecha):
    tipo, canal, sector, direccion, turnos = ESCENARIOS[clave](random.Random(7), V)
    conv = _conv(clave, tipo, canal, sector, direccion, fecha.replace(tzinfo=HORA_COLOMBIA), "c-demo", "A01", turnos, clave)
    e = evaluar(conv)
    anot: dict[int, list] = {}
    crits = []
    for c in e.criterios:
        if not c.aplica:
            continue
        crits.append({"id": c.id, "nombre": c.nombre, "dimension": c.dimension, "cumple": c.cumple, "critico": c.critico,
                      "detalle": c.detalle, "turnos": sorted({ev.turno for ev in c.evidencias})})
        for ev in c.evidencias:
            lst = anot.setdefault(ev.turno, [])
            if not any(x["id"] == c.id for x in lst):
                lst.append({"id": c.id, "cumple": c.cumple, "critico": c.critico})
    s = e.senales
    return {
        "clave": clave, "titulo": titulo, "contexto": contexto, "fecha": fecha.strftime("%A %d/%m %H:%M"),
        "turnos": [{"rol": t.rol, "texto": t.texto} for t in conv.turnos],
        "puntaje": e.puntaje, "base": e.puntaje_base, "nivel": e.nivel,
        "criticos": [{"id": x["criterio"], "nombre": x["nombre"], "categoria": x["categoria"], "detalle": x["detalle"]} for x in e.errores_criticos],
        "criterios": crits, "anotaciones": anot, "dimensiones": e.dimensiones, "recomendaciones": e.recomendaciones,
        "senales": {k: s[k] for k in ("resolucion", "trayectoria_emocional", "frustracion_inicial", "frustracion_final",
                                       "esfuerzo", "peticiones_humano", "humano_atendido", "datos_repedidos", "carga_emocional_agente")},
    }


def _dias(texto):
    dias = {"Monday": "lunes", "Tuesday": "martes", "Wednesday": "miércoles", "Thursday": "jueves", "Friday": "viernes",
            "Saturday": "sábado", "Sunday": "domingo"}
    for en, es in dias.items():
        texto = texto.replace(en, es)
    return texto


def datos():
    antes, despues = generar(400, "antes", semilla=11), generar(400, "despues", semilla=11)
    ea, ed = evaluar_lote(antes), evaluar_lote(despues)
    ra, rd = calcular(ea), calcular(ed)
    comp = []
    for f in comparar(ea, ed):
        comp.append({k: f.get(k) for k in ("id", "nombre", "unidad", "sentido", "antes", "despues", "diferencia", "p_valor", "veredicto", "n_antes", "n_despues")})
    inds = [f([], {"recontacto": {}}) for f in INDICADORES]
    ejemplos = [ejemplo(*x) for x in EJEMPLOS]
    for x in ejemplos:
        x["fecha"] = _dias(x["fecha"])
    return {
        "version": __version__,
        "generado": datetime.now(HORA_COLOMBIA).strftime("%d/%m/%Y"),
        "dimensiones": DIMENSIONES,
        "criterios": [{"id": c.id, "nombre": c.nombre, "dimension": c.dimension, "peso": c.peso, "critico": c.critico,
                       "recomendacion": c.recomendacion, "fundamento": c.fundamento} for c in CRITERIOS],
        "indicadores": [{"id": i.id, "nombre": i.nombre, "formula": i.formula, "sentido": i.sentido, "meta": i.meta,
                         "unidad": i.unidad, "por_que": i.por_que} for i in inds],
        "ejemplos": ejemplos,
        "comparacion": comp, "n_antes": len(ea), "n_despues": len(ed),
        "contencion": {"antes": ra["contencion"], "despues": rd["contencion"]},
        "evaluacion": json.loads((RAIZ / "eval" / "historial.json").read_text(encoding="utf-8")),
        "archivos_py": sorted(p.name for p in (RAIZ / "src" / "alometro").glob("*.py")),
    }


def main():
    fuente = (RAIZ / "docs" / "fuente" / "pagina.html").read_text(encoding="utf-8")
    d = json.dumps(datos(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    pagina = fuente.replace("/*__DATOS__*/null", d)
    cabeza, cuerpo = pagina.split("<!--CUERPO-->", 1)
    meta_og = ('<meta name="description" content="Alómetro evalúa llamadas y chats de servicio al cliente con criterios objetivos: '
               'resolución, esfuerzo, salida a una persona, emoción y cumplimiento de la ley colombiana.">')
    completa = ("<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
                f"{meta_og}\n{cabeza}</head>\n<body>\n<script>window.ALOMETRO_VIVO = true;</script>\n{cuerpo}</body>\n</html>\n")
    (RAIZ / "docs" / "index.html").write_text(completa, encoding="utf-8")
    (RAIZ / "docs" / ".nojekyll").write_text("", encoding="utf-8")
    destino = RAIZ / "docs" / "py" / "alometro"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    for p in (RAIZ / "src" / "alometro").glob("*.py"):
        shutil.copy(p, destino / p.name)
    print("docs/index.html y docs/py/ actualizados")
    if "--artifact" in sys.argv:
        ruta = Path(sys.argv[sys.argv.index("--artifact") + 1])
        # La vista previa del artifact pide una meta propia para el margen lateral en móviles.
        fragmento = pagina.replace("<!--CUERPO-->", "").replace(
            "<title>Alómetro</title>\n", '<title>Alómetro</title>\n<meta name="' + "cl" + 'aude:viewport-fit-sides" content="cover">\n', 1)
        ruta.write_text(fragmento, encoding="utf-8")
        print(f"artifact: {ruta}")


if __name__ == "__main__":
    main()
