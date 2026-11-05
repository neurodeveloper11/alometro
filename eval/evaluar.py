"""Precisión y sensibilidad de los detectores sobre el conjunto escrito a mano.

    python eval/evaluar.py eval/casos_v1.jsonl
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from alometro.cargar import desde_dict
from alometro.detectores import analizar

EXTRAER = {
    "peticion_humano": lambda s: bool(s.peticiones_humano),
    "humano_atendido": lambda s: s.humano_atendido is True,
    "bucle": lambda s: bool(s.bucles_bot) or len(s.fallbacks_bot) >= 2,
    "perdida_contexto": lambda s: bool(s.datos_repedidos),
    "resolucion": lambda s: s.resolucion,
    "queja": lambda s: s.queja is not None,
    "radicado": lambda s: s.radicado is not None,
    "credencial": lambda s: bool(s.pide_credencial),
    "coercion": lambda s: bool(s.coercion),
    "retencion": lambda s: s.retencion_antes_de_radicar is not None,
    "aceptacion": lambda s: s.aceptacion is not None,
    "amenaza_externa": lambda s: bool(s.amenazas_externas),
    "sin_respuesta": lambda s: s.sin_respuesta is not None,
    "trayectoria": lambda s: s.trayectoria,
}


def main(ruta):
    tabla = defaultdict(lambda: {"vp": 0, "fp": 0, "fn": 0, "vn": 0, "ok": 0, "n": 0})
    errores = []
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        d = json.loads(linea)
        esperado = d.pop("esperado")
        s = analizar(desde_dict(d))
        for k, v in esperado.items():
            obt = EXTRAER[k](s)
            t = tabla[k]
            t["n"] += 1
            if isinstance(v, bool):
                t["vp" if v and obt else "fn" if v else "fp" if obt else "vn"] += 1
            t["ok"] += obt == v
            if obt != v:
                errores.append(f"{d['id']}: {k} esperado={v} obtenido={obt}")
    print(f"{'Señal':18s} {'n':>3s} {'Exactitud':>9s} {'Precisión':>9s} {'Sensib.':>8s}")
    tot_ok = tot_n = 0
    for k, t in tabla.items():
        p = t["vp"] / (t["vp"] + t["fp"]) if t["vp"] + t["fp"] else None
        r = t["vp"] / (t["vp"] + t["fn"]) if t["vp"] + t["fn"] else None
        f = lambda x: "—" if x is None else f"{x:.2f}"
        print(f"{k:18s} {t['n']:>3d} {t['ok'] / t['n']:>9.2f} {f(p):>9s} {f(r):>8s}")
        tot_ok += t["ok"]
        tot_n += t["n"]
    print(f"\nExactitud global: {tot_ok}/{tot_n} = {tot_ok / tot_n:.2f}")
    if errores:
        print("\nErrores:\n  " + "\n  ".join(errores))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("casos_v1.jsonl")))
