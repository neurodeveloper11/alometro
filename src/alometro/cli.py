"""Línea de comandos de Alómetro.

    alometro demo                     # genera datos sintéticos y un informe de ejemplo
    alometro evaluar datos.jsonl -o informe.html --json resultados.json --csv resultados.csv --coaching coaching.csv
    alometro comparar antes.jsonl despues.jsonl
    alometro calibrar datos.jsonl etiquetas_humanas.csv
    alometro criterios                # imprime la rúbrica
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

from . import __version__
from .calibracion import calibrar, leer_etiquetas
from .cargar import a_jsonl, cargar
from .coaching import coaching_csv
from .estadistica import tamano_muestra
from .indicadores import calcular, comparar
from .informe import generar_html, resumen_json
from .motor import Politica, evaluar_lote
from .roles import leer_mapa
from .rubrica import CRITERIOS, DIMENSIONES
from .sintetico import generar

CLAVES_CONFIG = {"pesos", "desactivar", "metas", "anular_por_critico", "dias_recontacto"}


def _config(a) -> dict:
    """Lee el archivo de configuración JSON de la operación (opcional)."""
    if not getattr(a, "config", None):
        return {}
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    desconocidas = set(cfg) - CLAVES_CONFIG
    if desconocidas:
        raise SystemExit(f"Claves desconocidas en {a.config}: {', '.join(sorted(desconocidas))}. Válidas: {', '.join(sorted(CLAVES_CONFIG))}.")
    ids = {c.id for c in CRITERIOS}
    malos = (set(cfg.get("pesos", {})) | set(cfg.get("desactivar", []))) - ids
    if malos:
        raise SystemExit(f"Criterios desconocidos en {a.config}: {', '.join(sorted(malos))}.")
    return cfg


def _politica(a) -> Politica:
    cfg = _config(a)
    anular = cfg.get("anular_por_critico", True) and not a.no_anular
    return Politica(anular_por_critico=anular, anonimizar_evidencias=not a.sin_anonimizar,
                    pesos={k: int(v) for k, v in cfg.get("pesos", {}).items()}, desactivar=set(cfg.get("desactivar", [])))


def _csv(evs) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    ids = [c.id for c in CRITERIOS]
    w.writerow(["conversacion_id", "tipo", "canal", "agente_id", "puntaje", "puntaje_base", "nivel", "errores_criticos",
                "resolucion", "trayectoria", "esfuerzo", "carga_emocional", *ids])
    for e in evs:
        estado = {c.id: ("" if not c.aplica else int(bool(c.cumple))) for c in e.criterios}
        s = e.senales
        w.writerow([e.conversacion_id, e.tipo, e.canal, e.agente_id or "", e.puntaje, e.puntaje_base, e.nivel,
                    "|".join(x["criterio"] for x in e.errores_criticos), s["resolucion"], s["trayectoria_emocional"],
                    s["esfuerzo"], "" if s["carga_emocional_agente"] is None else s["carga_emocional_agente"],
                    *[estado.get(i, "") for i in ids]])
    return buf.getvalue()


def _imprimir_resumen(res: dict) -> None:
    print(f"\n{res['n']} interacciones evaluadas\n")
    print(f"{'Indicador':42s} {'Valor':>9s} {'Meta':>10s}  Estado")
    for i in res["indicadores"]:
        if i.valor is None:
            v = "—"
        elif i.unidad == "%":
            v = f"{100 * i.valor:.1f} %"
        else:
            v = f"{i.valor:.1f}"
        m = (">= " if i.sentido == "mayor" else "<= ") + (f"{100 * i.meta:g} %" if i.unidad == "%" else f"{i.meta:g}")
        est = {"cumple": "OK", "no_cumple": "NO", "sin_datos": "—"}[i.estado]
        print(f"{i.nombre[:42]:42s} {v:>9s} {m:>10s}  {est}  (n={i.n})")


def _cargar(a, ruta):
    convs = cargar(ruta, leer_mapa(getattr(a, "roles", None)))
    inferidas = [c for c in convs if c.metadatos.get("roles_inferidos")]
    dudosas = [c.id for c in inferidas if c.metadatos["roles_inferidos"].get("_confianza") == "baja"]
    if inferidas:
        print(f"Roles inferidos en {len(inferidas)} conversaciones con hablantes sin rol (p. ej. SPEAKER_00).", file=sys.stderr)
    if dudosas:
        print(f"Aviso: inferencia de roles con confianza baja en {len(dudosas)}: {', '.join(dudosas[:10])}. "
              "Revíselas o fije los roles con --roles SPEAKER_00=agente,SPEAKER_01=cliente.", file=sys.stderr)
    return convs


def cmd_evaluar(a) -> int:
    convs = _cargar(a, a.entrada)
    if not convs:
        print("No se encontraron conversaciones.", file=sys.stderr)
        return 1
    omitidas: list[str] = []
    evs = evaluar_lote(convs, _politica(a), omitidas)
    if omitidas:
        print(f"Aviso: se omitieron {len(omitidas)} conversaciones vacías: {', '.join(omitidas[:10])}"
              + (" …" if len(omitidas) > 10 else ""), file=sys.stderr)
    if not evs:
        print("No hay conversaciones con texto para evaluar.", file=sys.stderr)
        return 1
    cfg = _config(a)
    res = calcular(evs, dias_recontacto=cfg.get("dias_recontacto", a.dias_recontacto), metas=cfg.get("metas"))
    salida_html = a.salida or "informe_alometro.html"
    Path(salida_html).write_text(generar_html(evs, res, fuente=Path(a.entrada).name), encoding="utf-8")
    if a.json:
        Path(a.json).write_text(resumen_json(evs, res), encoding="utf-8")
    if a.csv:
        Path(a.csv).write_text(_csv(evs), encoding="utf-8")
    if a.coaching:
        Path(a.coaching).write_text(coaching_csv(res["coaching"]), encoding="utf-8")
    _imprimir_resumen(res)
    print(f"\nInforme: {salida_html}" + (f" · JSON: {a.json}" if a.json else "") + (f" · CSV: {a.csv}" if a.csv else "")
          + (f" · Coaching: {a.coaching}" if a.coaching else ""))
    if len(evs) < 100:
        print(f"Aviso: con {len(evs)} interacciones los porcentajes son poco precisos; "
              f"para ±5 puntos se necesitan unas {tamano_muestra()} por periodo.")
    return 0


def cmd_comparar(a) -> int:
    pol = _politica(a)
    antes, despues = evaluar_lote(_cargar(a, a.antes), pol), evaluar_lote(_cargar(a, a.despues), pol)
    filas = comparar(antes, despues, alfa=a.alfa)
    print(f"\nAntes: {len(antes)} interacciones · Después: {len(despues)} interacciones\n")
    print(f"{'Indicador':40s} {'Antes':>9s} {'Después':>9s} {'Cambio':>9s} {'p':>7s}  Veredicto")
    for f in filas:
        def fmt(x, pct=f["unidad"] == "%"):
            if x is None:
                return "—"
            return f"{100 * x:.1f}%" if pct else f"{x:.1f}"
        dif = "—" if f["diferencia"] is None else (f"{100 * f['diferencia']:+.1f}pp" if f["unidad"] == "%" else f"{f['diferencia']:+.1f}")
        p = "—" if f["p_valor"] is None else f"{f['p_valor']:.3f}"
        print(f"{f['nombre'][:40]:40s} {fmt(f['antes']):>9s} {fmt(f['despues']):>9s} {dif:>9s} {p:>7s}  {f['veredicto']}")
    if a.json:
        Path(a.json).write_text(json.dumps(filas, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return 0


def cmd_calibrar(a) -> int:
    convs = _cargar(a, a.entrada)
    evs = evaluar_lote(convs, _politica(a))
    etiquetas = leer_etiquetas(Path(a.etiquetas).read_text(encoding="utf-8-sig"))
    csat = {c.id: c.csat for c in convs if c.csat is not None}
    res = calibrar(evs, etiquetas, csat or None)
    print(f"\n{'Criterio':9s} {'n':>4s} {'Acuerdo':>8s} {'Kappa':>7s}  Interpretación   Apto")
    for f in res["criterios"]:
        k = "—" if f["kappa"] is None else f"{f['kappa']:.2f}"
        print(f"{f['criterio']:9s} {f['n']:>4d} {100 * f['acuerdo']:>7.1f}% {k:>7s}  {f['interpretacion']:15s} {'sí' if f['apto'] else 'no'}")
    if "validez_csat" in res and res["validez_csat"]["spearman"] is not None:
        v = res["validez_csat"]
        print(f"\nCorrelación puntaje-CSAT (Spearman): {v['spearman']:.2f} (n={v['n']})")
    print("\nRegla: un criterio es apto para decisiones con kappa ≥ 0,60 y n ≥ 20.")
    return 0


def cmd_demo(a) -> int:
    d = Path(a.carpeta)
    d.mkdir(parents=True, exist_ok=True)
    antes, despues = generar(a.n, "antes", semilla=a.semilla), generar(a.n, "despues", semilla=a.semilla)
    (d / "antes.jsonl").write_text(a_jsonl(antes), encoding="utf-8")
    (d / "despues.jsonl").write_text(a_jsonl(despues), encoding="utf-8")
    evs = evaluar_lote(antes)
    res = calcular(evs)
    (d / "informe_antes.html").write_text(generar_html(evs, res, titulo="Informe Alómetro · operación de ejemplo", fuente="datos sintéticos"), encoding="utf-8")
    evs2 = evaluar_lote(despues)
    (d / "informe_despues.html").write_text(generar_html(evs2, calcular(evs2), titulo="Informe Alómetro · después de las mejoras", fuente="datos sintéticos"), encoding="utf-8")
    print(f"Datos sintéticos en {d}/antes.jsonl y {d}/despues.jsonl")
    print(f"Informes: {d}/informe_antes.html y {d}/informe_despues.html")
    print(f"Pruebe: alometro comparar {d}/antes.jsonl {d}/despues.jsonl")
    return 0


def cmd_criterios(a) -> int:
    for dim, nombre in DIMENSIONES.items():
        print(f"\n== {nombre} ==")
        for c in CRITERIOS:
            if c.dimension == dim:
                tag = f"CRÍTICO ({c.critico})" if c.critico else f"{c.peso} pts"
                print(f"  {c.id:4s} {c.nombre:40s} {tag}")
                print(f"       Fundamento: {c.fundamento}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="alometro", description="Evaluación objetiva de call centers y chatbots (español de Colombia).")
    p.add_argument("--version", action="version", version=f"alometro {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def comunes(sp):
        sp.add_argument("--no-anular", action="store_true", help="no poner la nota en 0 cuando hay error crítico")
        sp.add_argument("--sin-anonimizar", action="store_true", help="mostrar las evidencias sin anonimizar")
        sp.add_argument("--roles", help="roles de hablantes sin nombre, p. ej. SPEAKER_00=agente,SPEAKER_01=cliente (si no, se infieren)")
        sp.add_argument("--config", help="JSON de la operación: pesos, desactivar, metas, anular_por_critico, dias_recontacto")

    e = sub.add_parser("evaluar", help="evaluar conversaciones y generar el informe")
    e.add_argument("entrada", help="archivo .xlsx/.csv/.tsv/.jsonl/.json/.txt/.srt/.vtt o carpeta")
    e.add_argument("-o", "--salida", help="informe HTML (por defecto informe_alometro.html)")
    e.add_argument("--json", help="guardar resultados completos en JSON")
    e.add_argument("--csv", help="guardar una fila por interacción en CSV")
    e.add_argument("--coaching", help="guardar el plan de coaching por agente en CSV")
    e.add_argument("--dias-recontacto", type=int, default=7)
    comunes(e)
    e.set_defaults(f=cmd_evaluar)

    c = sub.add_parser("comparar", help="¿mejoró de verdad? compara dos periodos")
    c.add_argument("antes")
    c.add_argument("despues")
    c.add_argument("--alfa", type=float, default=0.05)
    c.add_argument("--json")
    comunes(c)
    c.set_defaults(f=cmd_comparar)

    k = sub.add_parser("calibrar", help="acuerdo de Alómetro con evaluadores humanos (kappa)")
    k.add_argument("entrada")
    k.add_argument("etiquetas", help="CSV: conversacion_id,criterio,cumple")
    comunes(k)
    k.set_defaults(f=cmd_calibrar)

    d = sub.add_parser("demo", help="generar datos sintéticos e informes de ejemplo")
    d.add_argument("--carpeta", default="demo_alometro")
    d.add_argument("-n", type=int, default=240)
    d.add_argument("--semilla", type=int, default=11)
    d.set_defaults(f=cmd_demo)

    r = sub.add_parser("criterios", help="mostrar la rúbrica")
    r.set_defaults(f=cmd_criterios)

    a = p.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
