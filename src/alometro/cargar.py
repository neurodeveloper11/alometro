"""Carga de conversaciones desde JSON, JSONL, CSV o texto plano.

Formatos aceptados
------------------
JSON / JSONL (recomendado)::

    {"id": "c-001", "tipo": "servicio", "canal": "chat", "sector": "telecom",
     "direccion": "entrante", "inicio": "2026-10-03T14:22:00-05:00",
     "cliente_id": "h:9f2c", "agente_id": "A17", "csat": 4,
     "turnos": [{"rol": "cliente", "texto": "Hola", "t": 0.0}, ...]}

CSV (una fila por turno; las columnas de conversación se toman de la primera fila)::

    conversacion_id,rol,texto,t,tipo,canal,sector,direccion,inicio,cliente_id,agente_id,csat

Texto plano (una conversación por archivo; líneas «Rol: texto»)::

    # tipo: servicio | canal: voz | sector: telecom
    Agente: Buenas tardes, le habla Laura de ...
    Cliente: Hola, no tengo internet desde ayer
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from .modelos import Conversacion, Turno
from .roles import resolver

_CAMPOS_CONV = ("tipo", "canal", "sector", "direccion", "cliente_id", "agente_id")


def _fecha(valor: Any) -> datetime | None:
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor
    s = str(valor).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
    raise ValueError(f"Fecha no reconocida: {valor!r}")


def _float(valor: Any) -> float | None:
    if valor in (None, ""):
        return None
    return float(str(valor).replace(",", "."))


def desde_dict(d: dict, roles: dict[str, str] | None = None) -> Conversacion:
    """`roles` mapea etiquetas de hablante a roles (p. ej. {"SPEAKER_00": "agente"}); las desconocidas se infieren."""
    turnos_raw = d.get("turnos") or d.get("mensajes") or d.get("turns") or []
    etiquetas = [str(t.get("rol") or t.get("role") or t.get("speaker") or "") for t in turnos_raw]
    textos = [t.get("texto") or t.get("text") or "" for t in turnos_raw]
    resueltos, inferidos = resolver(etiquetas, textos, roles)
    turnos = [Turno(rol=r, texto=x, t=_float(t.get("t"))) for r, x, t in zip(resueltos, textos, turnos_raw)]
    meta = {k: v for k, v in d.items() if k not in {"id", "turnos", "mensajes", "turns", "inicio", "csat", *_CAMPOS_CONV}}
    if inferidos:
        meta["roles_inferidos"] = inferidos
    return Conversacion(
        id=str(d.get("id") or d.get("conversacion_id") or ""),
        turnos=turnos,
        tipo=d.get("tipo") or "servicio",
        canal=d.get("canal") or "voz",
        sector=d.get("sector") or "general",
        direccion=d.get("direccion"),
        inicio=_fecha(d.get("inicio")),
        cliente_id=d.get("cliente_id"),
        agente_id=d.get("agente_id"),
        csat=_float(d.get("csat")),
        metadatos=meta,
    )


def desde_jsonl(texto: str, roles: dict[str, str] | None = None) -> list[Conversacion]:
    return [desde_dict(json.loads(l), roles) for l in texto.splitlines() if l.strip()]


def desde_json(texto: str, roles: dict[str, str] | None = None) -> list[Conversacion]:
    data = json.loads(texto)
    if isinstance(data, dict):
        data = data.get("conversaciones", [data])
    return [desde_dict(d, roles) for d in data]


def desde_csv(texto: str, roles: dict[str, str] | None = None) -> list[Conversacion]:
    filas = list(csv.DictReader(io.StringIO(texto)))
    grupos: dict[str, list[dict]] = {}
    for f in filas:
        cid = f.get("conversacion_id") or f.get("id")
        if not cid:
            raise ValueError("El CSV necesita la columna 'conversacion_id'.")
        grupos.setdefault(cid, []).append(f)
    convs = []
    for cid, fs in grupos.items():
        p = fs[0]
        d = {k: p.get(k) for k in (*_CAMPOS_CONV, "inicio", "csat") if p.get(k)}
        d["id"] = cid
        d["turnos"] = [{"rol": f["rol"], "texto": f.get("texto", ""), "t": f.get("t")} for f in fs]
        convs.append(desde_dict(d, roles))
    return convs


_LINEA = re.compile(r"^\s*\[?(?P<t>\d{1,2}:\d{2}(:\d{2})?(\.\d+)?)?\]?\s*\[?(?P<rol>[A-Za-z0-9ÁÉÍÓÚáéíóúñÑ _\-]{1,24}?)\]?\s*:\s*(?P<texto>.+)$")
_VOZ_VTT = re.compile(r"^<v\s+(?P<rol>[^>]+)>(?P<texto>.*?)(</v>)?$")
_MARCA_SUB = re.compile(r"^(?P<ini>\d{1,2}:\d{2}(:\d{2})?[.,]\d{1,3})\s*-->\s*\S+")


def _segundos(marca: str | None) -> float | None:
    if not marca:
        return None
    partes = [float(x) for x in marca.replace(",", ".").split(":")]
    s = 0
    for p in partes:
        s = s * 60 + p
    return float(s)


def desde_txt(texto: str, id_: str = "txt-1", roles: dict[str, str] | None = None) -> Conversacion:
    meta: dict[str, str] = {}
    turnos: list[dict] = []
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        if linea.lstrip().startswith("#"):
            for par in linea.lstrip("# ").split("|"):
                if ":" in par:
                    k, v = par.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
            continue
        m = _LINEA.match(linea)
        if m:
            turnos.append({"rol": m.group("rol").strip(), "texto": m.group("texto").strip(), "t": _segundos(m.group("t"))})
        elif turnos:  # continuación del turno anterior
            turnos[-1]["texto"] += " " + linea.strip()
    if not turnos and texto.strip():
        raise ValueError(f"{id_}: no se encontraron turnos. Use una línea por turno con el formato «Hablante: texto».")
    d: dict[str, Any] = {"id": meta.pop("id", id_), "turnos": turnos, **meta}
    return desde_dict(d, roles)


def desde_subtitulos(texto: str, id_: str = "sub-1", roles: dict[str, str] | None = None) -> Conversacion:
    """SRT o WebVTT con hablantes («SPEAKER_00: hola» o «<v SPEAKER_00>hola»). Une los bloques seguidos del mismo hablante."""
    turnos: list[dict] = []
    t_actual: float | None = None
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.isdigit() or linea.upper().startswith(("WEBVTT", "NOTE", "STYLE")):
            continue
        m = _MARCA_SUB.match(linea)
        if m:
            t_actual = _segundos(m.group("ini").replace(",", "."))
            continue
        v = _VOZ_VTT.match(linea) or _LINEA.match(linea)
        if v:
            rol, txt = v.group("rol").strip(), v.group("texto").strip()
        elif turnos:
            turnos[-1]["texto"] += " " + linea
            continue
        else:
            raise ValueError(f"{id_}: el subtítulo no indica el hablante. Se espera «SPEAKER_00: texto» o «<v SPEAKER_00>texto».")
        if turnos and turnos[-1]["rol"] == rol:
            turnos[-1]["texto"] += " " + txt
        else:
            turnos.append({"rol": rol, "texto": txt, "t": t_actual})
    if not turnos:
        raise ValueError(f"{id_}: no se encontraron turnos en el subtítulo.")
    return desde_dict({"id": id_, "turnos": turnos}, roles)


FORMATOS = {".json", ".jsonl", ".csv", ".txt", ".srt", ".vtt"}


def cargar(ruta: str | Path, roles: dict[str, str] | None = None) -> list[Conversacion]:
    ruta = Path(ruta)
    if ruta.is_dir():
        convs: list[Conversacion] = []
        for f in sorted(ruta.iterdir()):
            if f.suffix.lower() in FORMATOS:
                convs.extend(cargar(f, roles))
        return convs
    texto = ruta.read_text(encoding="utf-8-sig")
    suf = ruta.suffix.lower()
    if suf == ".jsonl":
        return desde_jsonl(texto, roles)
    if suf == ".json":
        return desde_json(texto, roles)
    if suf == ".csv":
        return desde_csv(texto, roles)
    if suf == ".txt":
        return [desde_txt(texto, id_=ruta.stem, roles=roles)]
    if suf in (".srt", ".vtt"):
        return [desde_subtitulos(texto, id_=ruta.stem, roles=roles)]
    raise ValueError(f"Formato no soportado: {suf}")


def a_jsonl(convs: Iterable[Conversacion]) -> str:
    lineas = []
    for c in convs:
        d = {
            "id": c.id, "tipo": c.tipo, "canal": c.canal, "sector": c.sector, "direccion": c.direccion,
            "inicio": c.inicio.isoformat() if c.inicio else None, "cliente_id": c.cliente_id,
            "agente_id": c.agente_id, "csat": c.csat,
            "turnos": [{"rol": t.rol, "texto": t.texto, **({"t": t.t} if t.t is not None else {})} for t in c.turnos],
            **c.metadatos,
        }
        lineas.append(json.dumps({k: v for k, v in d.items() if v is not None}, ensure_ascii=False))
    return "\n".join(lineas) + "\n"
