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


# Nombres de columna habituales en exportaciones de CRM, centrales telefónicas y plataformas de chat.
_ALIAS_COLUMNAS = {
    "conversacion_id": ("conversacion_id", "id", "conversation_id", "conversation", "conversacion", "id_conversacion", "caso", "id_caso",
                        "ticket", "ticket_id", "chat_id", "call_id", "llamada", "id_llamada", "session_id", "sesion", "interaccion",
                        "id_interaccion", "interaction_id"),
    "rol": ("rol", "role", "speaker", "hablante", "emisor", "autor", "author", "from", "sender", "participante", "participant",
            "quien", "tipo_emisor", "remitente"),
    "texto": ("texto", "text", "message", "mensaje", "contenido", "content", "body", "utterance", "frase", "comentario"),
    "transcripcion": ("transcripcion", "transcript", "transcription", "conversacion_completa", "dialogo", "chat_completo"),
    "t": ("t", "segundo", "segundos", "offset", "start", "inicio_turno", "seconds"),
    "inicio": ("inicio", "fecha", "fecha_hora", "date", "datetime", "hora_inicio", "start_time", "created_at", "fecha_inicio", "timestamp"),
    "agente_id": ("agente_id", "agente", "agent", "agent_id", "asesor", "asesor_id", "id_asesor", "operador"),
    "cliente_id": ("cliente_id", "customer_id", "client_id", "id_cliente", "customer", "cliente"),
    "canal": ("canal", "channel"),
    "tipo": ("tipo", "type", "tipo_interaccion", "motivo_contacto", "campana", "campaign"),
    "sector": ("sector", "industria", "industry"),
    "direccion": ("direccion", "direction", "sentido"),
    "csat": ("csat", "satisfaccion", "satisfaction", "calificacion", "rating"),
}
_COLUMNA_CANONICA = {alias: canon for canon, aliases in _ALIAS_COLUMNAS.items() for alias in aliases}


def _clave_columna(nombre: str) -> str:
    from .texto import normalizar
    return re.sub(r"[^a-z0-9]+", "_", normalizar(nombre or "")).strip("_")


def _canonizar(filas: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """Renombra columnas a sus nombres canónicos. Devuelve (filas, {original: canónica})."""
    if not filas:
        return [], {}
    mapa: dict[str, str] = {}
    for col in filas[0]:
        canon = _COLUMNA_CANONICA.get(_clave_columna(col))
        if canon and canon not in mapa.values():
            mapa[col] = canon
    return [{mapa.get(k, k): v for k, v in f.items()} for f in filas], mapa


def _num_o_none(v: Any) -> float | None:
    try:
        return _float(v)
    except (TypeError, ValueError):
        return None


def _fecha_flexible(v: Any) -> datetime | None:
    if v in (None, ""):
        return None
    n = _num_o_none(v)
    if n is not None and 20000 < n < 80000:  # fecha serial de Excel
        from datetime import timedelta
        return datetime(1899, 12, 30) + timedelta(days=n)
    try:
        return _fecha(v)
    except ValueError:
        return None


def desde_filas(filas: list[dict], roles: dict[str, str] | None = None, origen: str = "tabla") -> list[Conversacion]:
    """Filas de una tabla (CSV o Excel). Acepta dos formas:

    * una fila por turno: columnas de conversación + rol + texto;
    * una fila por conversación: columna con la transcripción completa («Agente: …» por línea).
    """
    filas = [{k: (v.strip() if isinstance(v, str) else v) for k, v in f.items() if k is not None} for f in filas]
    filas = [f for f in filas if any(v not in (None, "") for v in f.values())]
    if not filas:
        return []
    filas, mapa = _canonizar(filas)
    cols = set(filas[0])
    meta_cols = (*_CAMPOS_CONV, "csat")
    if "transcripcion" in cols or ("texto" in cols and "rol" not in cols):
        col = "transcripcion" if "transcripcion" in cols else "texto"
        convs = []
        for i, f in enumerate(filas, 1):
            cid = str(f.get("conversacion_id") or f"{origen}-{i}")
            c = desde_txt(str(f.get(col) or ""), id_=cid, roles=roles)
            for k in meta_cols:
                if f.get(k) not in (None, ""):
                    setattr(c, k, _float(f[k]) if k == "csat" else str(f[k]).strip().lower() if k in ("tipo", "canal", "sector", "direccion") else str(f[k]))
            c.inicio = _fecha_flexible(f.get("inicio")) or c.inicio
            c.__post_init__()
            convs.append(c)
        return convs
    faltan = [c for c in ("conversacion_id", "rol", "texto") if c not in cols]
    if faltan:
        raise ValueError(
            f"{origen}: faltan columnas {faltan}. Columnas encontradas: {sorted(cols)}. Use una fila por turno con "
            "conversacion_id, rol y texto (también se aceptan id/speaker/message…), o una fila por conversación con una "
            "columna «transcripcion» de líneas «Agente: …» / «Cliente: …».")
    grupos: dict[str, list[dict]] = {}
    for f in filas:
        cid = str(f.get("conversacion_id") or "").strip()
        if not cid:
            continue
        grupos.setdefault(cid, []).append(f)
    convs = []
    for cid, fs in grupos.items():
        p = fs[0]
        d: dict[str, Any] = {k: p.get(k) for k in meta_cols if p.get(k) not in (None, "")}
        for k in ("tipo", "canal", "sector", "direccion"):
            if k in d:
                d[k] = str(d[k]).strip().lower()
        d["id"] = cid
        inicio = _fecha_flexible(p.get("inicio"))
        d["turnos"] = [{"rol": str(f.get("rol") or ""), "texto": str(f.get("texto") or ""), "t": _num_o_none(f.get("t"))} for f in fs]
        c = desde_dict(d, roles)
        c.inicio = inicio
        convs.append(c)
    return convs


def desde_csv(texto: str, roles: dict[str, str] | None = None, origen: str = "csv") -> list[Conversacion]:
    muestra = texto[:4096]
    try:
        dialecto = csv.Sniffer().sniff(muestra.splitlines()[0] if muestra else ",", delimiters=",;\t|")
    except csv.Error:
        dialecto = csv.excel
    return desde_filas(list(csv.DictReader(io.StringIO(texto), dialect=dialecto)), roles, origen)


def leer_xlsx(datos: bytes) -> list[dict]:
    """Primera hoja de un .xlsx como lista de dicts (biblioteca estándar: zip + XML)."""
    import zipfile
    from xml.etree import ElementTree as ET
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    try:
        z = zipfile.ZipFile(io.BytesIO(datos))
    except zipfile.BadZipFile as ex:
        raise ValueError("El archivo no es un Excel .xlsx válido (¿es un .xls antiguo? Guárdelo como .xlsx o .csv).") from ex
    compartidas: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
            compartidas.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
    libro = ET.fromstring(z.read("xl/workbook.xml"))
    hoja = libro.find("m:sheets/m:sheet", ns)
    rid = hoja.get(f"{{{ns['r']}}}id") if hoja is not None else None
    ruta = "xl/worksheets/sheet1.xml"
    if rid and "xl/_rels/workbook.xml.rels" in z.namelist():
        for rel in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")):
            if rel.get("Id") == rid:
                destino = rel.get("Target", "").lstrip("/")
                ruta = destino if destino.startswith("xl/") else "xl/" + destino
    filas: list[list[str]] = []
    for row in ET.fromstring(z.read(ruta)).iter(f"{{{ns['m']}}}row"):
        celdas: dict[int, str] = {}
        for c in row.findall("m:c", ns):
            ref = re.match(r"([A-Z]+)", c.get("r", "A"))
            col = 0
            for letra in ref.group(1) if ref else "A":
                col = col * 26 + (ord(letra) - 64)
            tipo, v = c.get("t"), c.find("m:v", ns)
            if tipo == "s" and v is not None:
                valor = compartidas[int(v.text)]
            elif tipo == "inlineStr":
                valor = "".join(t.text or "" for t in c.iter(f"{{{ns['m']}}}t"))
            else:
                valor = v.text if v is not None and v.text is not None else ""
            celdas[col - 1] = valor
        if celdas:
            fila = [""] * (max(celdas) + 1)
            for i, val in celdas.items():
                fila[i] = val
            filas.append(fila)
    if not filas:
        return []
    cab = [h.strip() or f"columna_{i + 1}" for i, h in enumerate(filas[0])]
    return [dict(zip(cab, f + [""] * (len(cab) - len(f)))) for f in filas[1:]]


def desde_xlsx(datos: bytes, roles: dict[str, str] | None = None, origen: str = "xlsx") -> list[Conversacion]:
    return desde_filas(leer_xlsx(datos), roles, origen)


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


FORMATOS = {".json", ".jsonl", ".csv", ".tsv", ".xlsx", ".txt", ".srt", ".vtt"}


def cargar(ruta: str | Path, roles: dict[str, str] | None = None) -> list[Conversacion]:
    ruta = Path(ruta)
    if ruta.is_dir():
        convs: list[Conversacion] = []
        for f in sorted(ruta.iterdir()):
            if f.suffix.lower() in FORMATOS:
                convs.extend(cargar(f, roles))
        return convs
    suf = ruta.suffix.lower()
    if suf == ".xlsx":
        return desde_xlsx(ruta.read_bytes(), roles, origen=ruta.name)
    datos = ruta.read_bytes()
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = datos.decode("cp1252")  # CSV exportados desde Excel en Windows
    if suf == ".jsonl":
        return desde_jsonl(texto, roles)
    if suf == ".json":
        return desde_json(texto, roles)
    if suf in (".csv", ".tsv"):
        return desde_csv(texto, roles, origen=ruta.name)
    if suf == ".txt":
        return [desde_txt(texto, id_=ruta.stem, roles=roles)]
    if suf in (".srt", ".vtt"):
        return [desde_subtitulos(texto, id_=ruta.stem, roles=roles)]
    raise ValueError(f"Formato no soportado: {suf}. Use uno de: {', '.join(sorted(FORMATOS))}.")


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
