"""Exactitud de la inferencia de roles en transcripciones con hablantes anónimos.

Toma conversaciones con roles conocidos (solo cliente y agente), reemplaza las etiquetas por
SPEAKER_00 / SPEAKER_01 en orden aleatorio y mide si Alómetro recupera quién es el agente.

    python eval/evaluar_roles.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from alometro.roles import resolver  # noqa: E402
from alometro.sintetico import generar  # noqa: E402


def conversaciones():
    """(origen, [(rol, texto)]) de los conjuntos escritos a mano y de la demo sintética."""
    for f in sorted(Path(__file__).parent.glob("casos_*.jsonl")):
        for linea in f.read_text(encoding="utf-8").splitlines():
            d = json.loads(linea)
            yield "escritos a mano", [(t["rol"], t["texto"]) for t in d["turnos"]]
    for c in generar(300, "antes", semilla=4):
        yield "sintéticos", [(t.rol, t.texto) for t in c.turnos]


def main():
    r = random.Random(7)
    res: dict[str, list[int]] = {}
    fallos = []
    for origen, turnos in conversaciones():
        turnos = [(rol, txt) for rol, txt in turnos if rol in ("cliente", "agente")]
        if {rol for rol, _ in turnos} != {"cliente", "agente"}:
            continue
        etiquetas = ["SPEAKER_00", "SPEAKER_01"]
        r.shuffle(etiquetas)
        mapa = {"agente": etiquetas[0], "cliente": etiquetas[1]}
        anon = [mapa[rol] for rol, _ in turnos]
        roles, _ = resolver(anon, [t for _, t in turnos])
        ok = roles == [rol for rol, _ in turnos]
        res.setdefault(origen, [0, 0])
        res[origen][0] += ok
        res[origen][1] += 1
        if not ok and origen == "escritos a mano":
            fallos.append(" | ".join(f"{rol}: {txt[:40]}" for rol, txt in turnos[:2]))
    for origen, (ok, n) in res.items():
        print(f"{origen:16s} {ok}/{n} = {ok / n:.2f}")
    if fallos:
        print("\nFallos (escritos a mano):\n  " + "\n  ".join(fallos))


if __name__ == "__main__":
    main()
