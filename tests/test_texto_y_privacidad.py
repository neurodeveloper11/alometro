from alometro.privacidad import anonimizar, anonimizar_texto
from alometro.texto import jaccard, luhn_valido, normalizar
from conftest import conv


def test_normalizar():
    assert normalizar("  ¿Está  ACÁ el señor?") == "¿esta aca el senor?"


def test_jaccard():
    assert jaccard("hola como estas", "hola como estas") == 1.0
    assert jaccard("a b", "c d") == 0.0


def test_luhn():
    assert luhn_valido("4111 1111 1111 1111")
    assert not luhn_valido("4111 1111 1111 1112")


def test_anonimiza_datos_comunes():
    t = anonimizar_texto("Soy CC 1.023.456.789, cel 300 123 4567, correo ana@x.co, tarjeta 4111 1111 1111 1111, vivo en Calle 10 # 5-20")
    for dato in ("1.023.456.789", "300 123 4567", "ana@x.co", "4111", "Calle 10"):
        assert dato not in t
    assert "[CORREO]" in t and "[TARJETA]" in t


def test_conserva_radicados():
    c = anonimizar(conv([("agente", "Su radicado es 43-1234567890 y su cédula 1.023.456.789")]))
    assert "43-1234567890" in c.turnos[0].texto
    assert "1.023.456.789" not in c.turnos[0].texto


def test_negaciones():
    from alometro import lexicos as L
    from alometro.texto import buscar_afirmado, normalizar
    no = lambda t, pats: buscar_afirmado(pats, normalizar(t)) is None  # noqa: E731
    assert no("no necesito un asesor, solo mi saldo", L.PETICION_HUMANO)
    assert no("no voy a poner ninguna queja en la superintendencia", L.AMENAZA_EXTERNA)
    assert no("no estoy molesta", L.FRUSTRACION_LEVE)
    assert no("no, no acepto", L.ACEPTACION_CLIENTE)
    # El «no» de otra frase no niega la petición.
    assert not no("el bot no entiende, páseme con un asesor", L.PETICION_HUMANO)
    assert not no("no sé qué pasa pero quiero hablar con una persona", L.PETICION_HUMANO)
    assert not no("sí, acepto", L.ACEPTACION_CLIENTE)
