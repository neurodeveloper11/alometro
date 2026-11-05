"""Genera CRITERIOS.md desde la rúbrica del código (fuente única de verdad)."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from alometro.indicadores import INDICADORES
from alometro.rubrica import CRITERIOS, DIMENSIONES

lineas = [
    "# Criterios y metas de Alómetro", "",
    "> Archivo generado por `scripts/generar_criterios_md.py` a partir de `src/alometro/rubrica.py` e `indicadores.py`. No editar a mano.", "",
    "## Cómo se calcula la nota", "",
    "* Cada criterio declara **cuándo aplica**, **qué es cumplir** y **qué evidencia** lo respalda (turno y cita).",
    "* Nota base = 100 × puntos de los criterios cumplidos / puntos de los criterios que aplican. Lo que no aplica no suma ni resta.",
    "* Los **errores críticos** (peso 0, marcados ⛔) se cuentan aparte en tres categorías: *cliente*, *negocio* y *cumplimiento*.",
    "  Por defecto anulan la nota de la interacción (nivel «Crítico»). Se puede desactivar con `--no-anular`.",
    "* Niveles: Excelente ≥ 90 · Bueno ≥ 75 · Mejorable ≥ 60 · Deficiente < 60 · Crítico = hay error crítico.", "",
    "## Criterios de revisión (por interacción)", "",
]
for dim, nombre in DIMENSIONES.items():
    lineas += [f"### {nombre}", "", "| Id | Criterio | Peso | Qué hacer si falla | Fundamento |", "|---|---|---|---|---|"]
    for c in CRITERIOS:
        if c.dimension == dim:
            peso = f"⛔ crítico ({c.critico})" if c.critico else str(c.peso)
            lineas.append(f"| {c.id} | {c.nombre} | {peso} | {c.recomendacion} | {c.fundamento} |")
    lineas.append("")
lineas += [
    "## Criterios de resultado (¿se está logrando el objetivo?)", "",
    "Se calculan sobre el conjunto de interacciones, con intervalo de confianza del 95 % (Wilson).",
    "Las metas son **puntos de partida**; fíjelas con 4 semanas de línea base de su operación.", "",
    "| Id | Indicador | Fórmula | Meta | Por qué importa |", "|---|---|---|---|---|",
]
ctx_dummy = {"recontacto": {}}
for f in INDICADORES:
    i = f([], ctx_dummy)
    sig = "≥" if i.sentido == "mayor" else "≤"
    meta = f"{100 * i.meta:g} %" if i.unidad == "%" else f"{i.meta:g} {i.unidad}"
    lineas.append(f"| {i.id} | {i.nombre} | {i.formula} | {sig} {meta} | {i.por_que} |")
lineas += [
    "", "## Criterios para verificar que la herramienta mide bien", "",
    "| Verificación | Cómo | Umbral |", "|---|---|---|",
    "| Acuerdo con analistas humanos | `alometro calibrar` (kappa de Cohen por criterio, ≥ 50 interacciones doble-calificadas) | κ ≥ 0,60 y n ≥ 20 por criterio para usarlo en decisiones |",
    "| Precisión de los detectores | `python eval/evaluar.py` sobre conjuntos escritos a mano, incluido uno ciego | Reportar siempre la cifra del conjunto ciego |",
    "| Validez frente al cliente | Correlación de Spearman entre el puntaje y la encuesta CSAT | ρ > 0 y creciente en el tiempo |",
    "| Validez frente al resultado | Recontacto a 7 días de las interacciones «resueltas» vs. «no resueltas» | Recontacto menor en las «resueltas» |",
    "| Mejora real, no ruido | `alometro comparar antes despues` (IC 95 % y p-valor por indicador) | p < 0,05 en la dirección deseada |",
    "",
]
(RAIZ / "CRITERIOS.md").write_text("\n".join(lineas), encoding="utf-8")
print("CRITERIOS.md generado")
