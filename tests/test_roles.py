import pytest

from alometro.cargar import cargar, desde_dict, desde_subtitulos, desde_txt
from alometro.cli import main
from alometro.roles import leer_mapa, resolver

SRT = """1
00:00:00,000 --> 00:00:03,000
SPEAKER_00: hola, me cobraron dos veces la factura y quiero el reembolso

2
00:00:03,500 --> 00:00:08,000
SPEAKER_01: Buenas tardes, le habla Laura. Lamento lo ocurrido, para su seguridad ¿me confirma su cédula?

3
00:00:08,500 --> 00:00:09,000
SPEAKER_00: 1020304050
"""


def test_srt_infiere_agente_aunque_el_cliente_hable_primero():
    c = desde_subtitulos(SRT, "x")
    assert [t.rol for t in c.turnos] == ["cliente", "agente", "cliente"]
    assert c.metadatos["roles_inferidos"]["speaker_01"] == "agente"
    assert c.turnos[1].t == 3.5


def test_vtt_con_voces_y_bloques_unidos():
    vtt = "WEBVTT\n\n00:00.000 --> 00:02.000\n<v Hablante 2>Buenos días, mi nombre es Paola, ¿en qué le puedo ayudar?\n\n" \
          "00:02.000 --> 00:04.000\n<v Hablante 2>Esta llamada puede ser grabada.\n\n00:04.000 --> 00:06.000\n<v Hablante 1>no tengo internet\n"
    c = desde_subtitulos(vtt, "v")
    assert [t.rol for t in c.turnos] == ["agente", "cliente"]  # los dos bloques seguidos del agente se unen


def test_mapa_manual_gana_a_la_inferencia():
    c = desde_txt("spk_0: hola, quiero cancelar\nspk_1: buenas, le habla Ana", roles=leer_mapa("spk_0=agente,spk_1=cliente"))
    assert [t.rol for t in c.turnos] == ["agente", "cliente"]
    assert "roles_inferidos" not in c.metadatos


def test_roles_conocidos_no_se_infieren():
    c = desde_dict({"id": "a", "turnos": [{"rol": "Agent", "texto": "hola"}, {"rol": "customer", "texto": "hola"}]})
    assert [t.rol for t in c.turnos] == ["agente", "cliente"] and "roles_inferidos" not in c.metadatos


def test_confianza_baja_en_fragmentos_ambiguos():
    _, inf = resolver(["A", "B"], ["ok", "ok"])
    assert inf.get("_confianza") == "baja"


def test_errores_claros():
    with pytest.raises(ValueError):
        leer_mapa("SPEAKER_00=jefe")
    with pytest.raises(ValueError):
        desde_txt("texto sin hablantes")


def test_cli_con_srt_y_roles(tmp_path, capsys):
    f = tmp_path / "llamada.srt"
    f.write_text(SRT, encoding="utf-8")
    assert len(cargar(tmp_path)) == 1  # las carpetas incluyen .srt
    assert main(["evaluar", str(f), "-o", str(tmp_path / "i.html"), "--roles", "SPEAKER_01=agente,SPEAKER_00=cliente"]) == 0
