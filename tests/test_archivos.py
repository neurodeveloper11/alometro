"""Archivos reales de empresas: CSV con «;», encabezados de CRM, Excel y una fila por conversación."""

import io
import zipfile

import pytest

from alometro.cargar import cargar, desde_csv, desde_xlsx, leer_xlsx
from alometro.motor import evaluar_lote


def _xlsx(filas: list[list]) -> bytes:
    """Excel mínimo válido con cadenas en línea (sin depender de openpyxl)."""
    def celda(ref, v):
        if isinstance(v, (int, float)):
            return f'<c r="{ref}"><v>{v}</v></c>'
        v = str(v).replace("&", "&amp;").replace("<", "&lt;")
        return f'<c r="{ref}" t="inlineStr"><is><t>{v}</t></is></c>'
    letras = "ABCDEFGHIJ"
    filas_xml = "".join(
        f'<row r="{i + 1}">' + "".join(celda(f"{letras[j]}{i + 1}", v) for j, v in enumerate(f)) + "</row>" for i, f in enumerate(filas))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   '<sheet name="Datos" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   f"<sheetData>{filas_xml}</sheetData></worksheet>")
    return buf.getvalue()


CRM = ("Conversation ID;Speaker;Message;Agent;Channel\n"
       "T-1;bot;Hola, soy el asistente virtual;;whatsapp\n"
       "T-1;customer;quiero hablar con un asesor;;whatsapp\n"
       "T-1;agent;Hola, le habla Ana. ¿En qué le ayudo?;A7;whatsapp\n"
       "T-2;customer;no tengo internet;;chat\n"
       "T-2;agent;Listo, ya quedó restablecido el servicio;A7;chat\n")


def test_csv_de_crm_con_punto_y_coma_y_encabezados_en_ingles():
    convs = desde_csv(CRM)
    assert [c.id for c in convs] == ["T-1", "T-2"]
    assert [t.rol for t in convs[0].turnos] == ["bot", "cliente", "agente"]
    assert convs[0].canal == "whatsapp" and convs[0].agente_id is None or convs[0].agente_id == ""
    assert evaluar_lote(convs)[1].senales["resolucion"] == "resuelto"


def test_una_fila_por_conversacion_con_transcripcion():
    texto = ('id_llamada,Transcripción,Fecha,Asesor,Satisfacción\n'
             'L-9,"Agente: Buenas tardes, le habla Laura\nCliente: me cobraron doble\nAgente: Le radiqué el reclamo con el número 2026-1188",'
             '2026-10-14 10:30,A3,4\n')
    c = desde_csv(texto)[0]
    assert c.id == "L-9" and c.agente_id == "A3" and c.csat == 4.0 and c.inicio.hour == 10
    assert [t.rol for t in c.turnos] == ["agente", "cliente", "agente"]


def test_excel_con_fecha_serial_y_roles_anonimos():
    datos = _xlsx([["Caso", "Hablante", "Mensaje", "Fecha"],
                   ["C1", "SPEAKER_00", "Buenos días, mi nombre es Paola, ¿en qué le puedo ayudar?", 46309.4375],
                   ["C1", "SPEAKER_01", "no tengo luz desde ayer", 46309.4375]])
    assert leer_xlsx(datos)[0]["Hablante"] == "SPEAKER_00"
    c = desde_xlsx(datos)[0]
    assert [t.rol for t in c.turnos] == ["agente", "cliente"]
    assert c.inicio.year == 2026 and c.inicio.month == 10 and c.inicio.day == 14 and c.inicio.hour == 10  # serial 46309 = 14-oct-2026


def test_excel_real_de_openpyxl(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["conversacion_id", "rol", "texto"])
    ws.append(["X", "cliente", "hola, ¿a qué hora abren?"])
    ws.append(["X", "agente", "De 8 a 5, señora."])
    f = tmp_path / "datos.xlsx"
    wb.save(f)
    convs = cargar(f)
    assert len(convs) == 1 and convs[0].turnos[1].rol == "agente"


def test_csv_en_codificacion_de_windows(tmp_path):
    f = tmp_path / "export.csv"
    f.write_bytes("conversacion_id;rol;texto\nA;cliente;¿Cuándo llega mi pedido?\nA;agente;Mañana, señor.\n".encode("cp1252"))
    assert cargar(f)[0].turnos[0].texto.startswith("¿Cuándo")


def test_errores_explican_que_falta():
    with pytest.raises(ValueError, match="faltan columnas"):
        desde_csv("nombre,valor\nx,1\n")
    with pytest.raises(ValueError, match="xlsx válido"):
        desde_xlsx(b"esto no es excel")
