"""Informe HTML autocontenido (sin dependencias externas, funciona sin internet)."""

from __future__ import annotations

import html
import json
from datetime import datetime

from .calendario import HORA_COLOMBIA
from .indicadores import Indicador
from .modelos import Evaluacion
from .rubrica import CRITERIOS_POR_ID, DIMENSIONES

E = html.escape

_CSS = """
:root{--bg:#f6f5f2;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#7a7974;--line:#e1e0d9;--axis:#c3c2b7;
--accent:#2a78d6;--good:#0ca30c;--good-ink:#006300;--bad:#d03b3b;--warn:#fab219;--chip:#eeede8;color-scheme:light}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){--bg:#121211;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;
--muted:#9b9a93;--line:#2c2c2a;--axis:#383835;--accent:#3987e5;--good-ink:#0ca30c;--chip:#262624;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121211;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#9b9a93;--line:#2c2c2a;--axis:#383835;
--accent:#3987e5;--good-ink:#0ca30c;--chip:#262624;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1120px;margin:0 auto;padding:24px 16px 64px}h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 12px}
h3{font-size:15px;margin:0 0 6px}.sub{color:var(--ink2);margin:0 0 20px}.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}.kpi .v{font-size:28px;font-weight:650;font-variant-numeric:tabular-nums}
.kpi .n{color:var(--muted);font-size:12.5px}.kpi .f{color:var(--ink2);font-size:13px;margin-top:6px}
.st{display:inline-flex;gap:6px;align-items:center;font-size:12.5px;font-weight:600;padding:2px 8px;border-radius:99px;background:var(--chip)}
.st i{width:8px;height:8px;border-radius:50%;display:inline-block}.ok i{background:var(--good)}.no i{background:var(--bad)}.nd i{background:var(--axis)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--ink2);font-weight:600;font-size:12.5px}td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.bar{height:10px;background:var(--line);border-radius:4px;min-width:120px;position:relative}.bar b{position:absolute;left:0;top:0;bottom:0;background:var(--accent);border-radius:4px}
.wrap{overflow-x:auto}.chip{display:inline-block;background:var(--chip);border-radius:6px;padding:1px 7px;font-size:12.5px;margin:1px 2px 1px 0}
.crit{color:var(--bad);font-weight:600}details{border-top:1px solid var(--line);padding:10px 0}summary{cursor:pointer;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.pill{font-weight:700;font-variant-numeric:tabular-nums;min-width:44px;text-align:center;border-radius:8px;padding:2px 6px;background:var(--chip)}
.ev{color:var(--ink2);font-size:13.5px;margin:2px 0 2px 14px}.ev em{color:var(--muted);font-style:normal}.muted{color:var(--muted)}
.rec{margin:6px 0 0 0;padding-left:18px;color:var(--ink2)}footer{margin-top:40px;color:var(--muted);font-size:13px}
.two{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
"""


def _pct(x: float | None, dec: int = 0) -> str:
    return "—" if x is None else f"{100 * x:.{dec}f} %"


def _valor(ind: Indicador) -> str:
    if ind.valor is None:
        return "—"
    if ind.unidad == "%":
        return _pct(ind.valor, 1)
    return f"{ind.valor:.1f}" if ind.unidad == "pts" else f"{ind.valor:g}"


def _meta(ind: Indicador) -> str:
    sig = "≥" if ind.sentido == "mayor" else "≤"
    m = f"{100 * ind.meta:g} %" if ind.unidad == "%" else f"{ind.meta:g}"
    return f"Meta {sig} {m}"


def _estado(estado: str) -> str:
    cls, txt = {"cumple": ("ok", "✓ Cumple"), "no_cumple": ("no", "✕ No cumple")}.get(estado, ("nd", "Sin datos"))
    return f'<span class="st {cls}"><i></i>{txt}</span>'


def _barra(x: float | None, titulo: str = "") -> str:
    w = 0 if x is None else max(0, min(100, 100 * x))
    return f'<div class="bar" title="{E(titulo)}"><b style="width:{w:.1f}%"></b></div>'


def generar_html(evs: list[Evaluacion], resumen: dict, titulo: str = "Informe Alómetro", fuente: str = "") -> str:
    inds: list[Indicador] = resumen["indicadores"]
    partes = [f"<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
              f"<title>{E(titulo)}</title><style>{_CSS}</style></head><body><main>"]
    partes.append(f"<h1>{E(titulo)}</h1><p class='sub'>{resumen['n']} interacciones evaluadas"
                  f"{(' · ' + E(fuente)) if fuente else ''} · generado el {datetime.now(HORA_COLOMBIA):%d/%m/%Y %H:%M} (hora de Colombia). "
                  "Las metas son puntos de partida: ajústelas con la línea base de su operación.</p>")

    # --- Indicadores ---
    cumplen = sum(1 for i in inds if i.estado == "cumple")
    con_datos = sum(1 for i in inds if i.estado != "sin_datos")
    partes.append(f"<h2>¿Estamos logrando el objetivo? <span class='muted' style='font-weight:400'>({cumplen} de {con_datos} indicadores en meta)</span></h2><div class='grid'>")
    for i in inds:
        ic = ""
        if i.ic95 and i.unidad == "%":
            ic = f" · IC 95 %: {_pct(i.ic95[0], 1)}–{_pct(i.ic95[1], 1)}"
        elif i.ic95:
            ic = f" · IC 95 %: {i.ic95[0]:.1f}–{i.ic95[1]:.1f}"
        partes.append(f"<div class='card kpi'><h3>{E(i.nombre)}</h3><div class='v'>{_valor(i)}</div>{_estado(i.estado)}"
                      f"<div class='n'>{_meta(i)} · n = {i.n}{ic}</div><div class='f'>{E(i.por_que)}</div></div>")
    partes.append("</div>")

    c = resumen["contencion"]
    if c["conversaciones_con_bot"]:
        partes.append("<h2>Contención del bot: aparente vs. real</h2><div class='card'><p>De "
                      f"{c['conversaciones_con_bot']} conversaciones con bot, el <b>{_pct(c['contencion_bruta'], 1)}</b> nunca pasó a una persona "
                      f"(contención aparente), pero solo el <b>{_pct(c['contencion_real'], 1)}</b> terminó resuelto y sin recontacto "
                      "(contención real). La diferencia son clientes que se rindieron o volvieron por otro canal.</p></div>")

    # --- Errores críticos ---
    criticos: dict[str, int] = {}
    for e in evs:
        for x in e.errores_criticos:
            criticos[x["criterio"]] = criticos.get(x["criterio"], 0) + 1
    if criticos:
        partes.append("<h2>Errores críticos</h2><div class='card wrap'><table><tr><th>Criterio</th><th>Categoría</th><th>Interacciones</th><th>Fundamento</th></tr>")
        for cid, n in sorted(criticos.items(), key=lambda x: -x[1]):
            cr = CRITERIOS_POR_ID[cid]
            partes.append(f"<tr><td><b>{cid}</b> {E(cr.nombre)}</td><td>{E(cr.critico or '')}</td><td class='num'>{n}</td><td class='muted'>{E(cr.fundamento)}</td></tr>")
        partes.append("</table></div>")

    # --- Criterios ---
    partes.append("<h2>Cumplimiento por criterio (de peor a mejor)</h2><div class='card wrap'><table><tr><th>Criterio</th><th>Dimensión</th><th>Aplica</th><th>Cumple</th><th style='min-width:160px'></th></tr>")
    for f in resumen["criterios"]:
        marca = " <span class='crit'>crítico</span>" if f["critico"] else ""
        etiqueta = "{}: {}".format(f["id"], _pct(f["tasa"]))
        partes.append(f"<tr><td><b>{f['id']}</b> {E(f['nombre'])}{marca}</td><td>{E(DIMENSIONES[f['dimension']])}</td>"
                      f"<td class='num'>{f['aplica']}</td><td class='num'>{_pct(f['tasa'])}</td><td>{_barra(f['tasa'], etiqueta)}</td></tr>")
    partes.append("</table></div>")

    # --- Temas y modalidad ---
    partes.append("<div class='two'><div><h2>Temas recurrentes</h2><div class='card wrap'><table><tr><th>Tema</th><th>n</th><th>Resolución</th><th style='min-width:140px'></th></tr>")
    for t in resumen["temas"][:14]:
        partes.append(f"<tr><td>{E(t['tema'].replace('_', ' '))}</td><td class='num'>{t['n']}</td><td class='num'>{_pct(t['resolucion'])}</td>"
                      f"<td>{_barra(t['resolucion'], 'Resolución ' + _pct(t['resolucion']))}</td></tr>")
    partes.append("</table></div></div><div><h2>Por modalidad de atención</h2><div class='card wrap'><table><tr><th>Modalidad</th><th>n</th><th>Puntaje</th><th>Con error crítico</th></tr>")
    for m in resumen["por_modalidad"]:
        partes.append(f"<tr><td>{E(m['modalidad'])}</td><td class='num'>{m['n']}</td><td class='num'>{m['puntaje_promedio']}</td><td class='num'>{m['con_error_critico']}</td></tr>")
    partes.append("</table></div></div></div>")

    # --- Agentes ---
    if resumen["agentes"]:
        partes.append("<h2>Agentes: calidad y carga emocional</h2><div class='card wrap'><table><tr><th>Agente</th><th>n</th><th>Puntaje</th><th>Con error crítico</th><th>Carga emocional</th><th>Interacciones hostiles</th><th>Alerta</th></tr>")
        for a in resumen["agentes"]:
            alerta = "<span class='st no'><i></i>Revisar riesgo psicosocial</span>" if a["alerta_psicosocial"] else "<span class='muted'>—</span>"
            partes.append(f"<tr><td>{E(a['agente_id'])}</td><td class='num'>{a['n']}</td><td class='num'>{a['puntaje_promedio']}</td><td class='num'>{a['con_error_critico']}</td>"
                          f"<td class='num'>{a['carga_emocional_promedio']}</td><td class='num'>{a['interacciones_hostiles']}</td><td>{alerta}</td></tr>")
        partes.append("</table><p class='muted'>La carga emocional (0-100) suma insultos, amenazas y frustración intensa que recibe el agente. "
                      "Un 25 % o más de interacciones hostiles es una demanda emocional alta: considere pausas de recuperación y acompañamiento "
                      "(la batería de riesgo psicosocial, Res. 2764 de 2022, evalúa las demandas emocionales).</p></div>")

    # --- Ley 2300 ---
    if resumen["ley_2300_frecuencia"]:
        partes.append("<h2>Alertas de frecuencia de contacto (Ley 2300 de 2023)</h2><div class='card wrap'><table><tr><th>Cliente</th><th>Regla</th><th>Detalle</th></tr>")
        for a in resumen["ley_2300_frecuencia"]:
            det = a.get("fecha") or a.get("semana")
            extra = ", ".join(a.get("canales", a.get("conversaciones", [])))
            partes.append(f"<tr><td>{E(a['cliente_id'])}</td><td>{E(a['regla'])}</td><td>{E(str(det))}: {E(extra)}</td></tr>")
        partes.append("</table></div>")

    # --- Interacciones ---
    partes.append("<h2>Interacciones (de menor a mayor puntaje)</h2><div class='card'>")
    for e in sorted(evs, key=lambda x: (x.puntaje, x.puntaje_base))[:300]:
        crit = " ".join(f"<span class='chip crit'>{E(x['criterio'])}</span>" for x in e.errores_criticos)
        modal = "bot → persona" if e.senales.get("hubo_bot") and e.senales.get("hubo_agente") else "solo bot" if e.senales.get("hubo_bot") else "persona"
        partes.append(f"<details><summary><span class='pill'>{e.puntaje}</span><b>{E(e.conversacion_id)}</b>"
                      f"<span class='chip'>{E(e.tipo)}</span><span class='chip'>{E(e.canal)}</span><span class='chip'>{E(modal)}</span>"
                      f"<span class='muted'>{E(e.nivel)} · base {e.puntaje_base} · {E(e.senales['resolucion'].replace('_', ' '))} · emoción {E(e.senales['trayectoria_emocional'])}</span>{crit}</summary>")
        fallas = [r for r in e.criterios if r.aplica and r.cumple is False]
        for r in fallas:
            partes.append(f"<div><b class='{'crit' if r.critico else ''}'>{r.id}</b> {E(r.nombre)}: {E(r.detalle)}</div>")
            for ev in r.evidencias[:3]:
                partes.append(f"<div class='ev'><em>Turno {ev.turno} · {E(ev.rol)}:</em> «{E(ev.cita)}»</div>")
        if not fallas:
            partes.append("<div class='muted'>Cumple todos los criterios aplicables.</div>")
        if e.recomendaciones:
            partes.append("<ul class='rec'>" + "".join(f"<li>{E(x)}</li>" for x in e.recomendaciones) + "</ul>")
        partes.append("</details>")
    partes.append("</div>")
    partes.append("<footer>Alómetro evalúa con reglas explícitas y auditables; cada hallazgo cita el turno que lo respalda. "
                  "Las evidencias se anonimizan. Antes de usar los puntajes para decisiones sobre personas, calibre con evaluadores humanos (alometro calibrar).</footer>")
    partes.append("</main></body></html>")
    return "".join(partes)


def resumen_json(evs: list[Evaluacion], resumen: dict) -> str:
    salida = {**resumen, "indicadores": [i.a_dict() for i in resumen["indicadores"]], "evaluaciones": [e.a_dict() for e in evs]}
    return json.dumps(salida, ensure_ascii=False, indent=2, default=str)
