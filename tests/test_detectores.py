from alometro.detectores import analizar
from conftest import conv


def test_peticion_humano_no_atendida_y_bucle():
    s = analizar(conv([
        ("bot", "Hola, escribe una opción: 1. Facturas 2. Soporte"),
        ("cliente", "quiero hablar con un asesor"),
        ("bot", "Lo siento, no te entendí. Escribe una opción: 1. Facturas 2. Soporte"),
        ("cliente", "ASESOR"),
        ("bot", "Lo siento, no te entendí. Escribe una opción: 1. Facturas 2. Soporte"),
    ]))
    assert len(s.peticiones_humano) == 2
    assert s.humano_atendido is False
    assert s.bucles_bot and len(s.fallbacks_bot) >= 2
    assert s.bot_se_identifica is False


def test_peticion_humano_atendida_rapido():
    s = analizar(conv([
        ("bot", "Soy el asistente virtual. ¿En qué te ayudo?"),
        ("cliente", "Necesito un asesor por favor"),
        ("bot", "Claro, te comunico con un asesor."),
        ("agente", "Hola, le habla Ana."),
    ]))
    assert s.humano_atendido is True and s.pasos_bot_hasta_humano == 1
    assert s.bot_se_identifica


def test_peticion_con_persona_ya_presente_no_cuenta():
    s = analizar(conv([("agente", "Buenas, le habla Ana"), ("cliente", "quiero hablar con un supervisor o con otra persona")]))
    assert s.peticiones_humano == []


def test_menciones_que_no_son_peticion():
    s = analizar(conv([("bot", "Hola"), ("cliente", "un asesor me dijo que el cobro se reversaba")]))
    assert s.peticiones_humano == []


def test_perdida_de_contexto_en_traspaso():
    s = analizar(conv([
        ("bot", "Por favor escribe tu número de cédula."),
        ("cliente", "1023456789"),
        ("bot", "Te comunico con un asesor."),
        ("agente", "Buenas, me regala su número de cédula por favor"),
    ]))
    assert len(s.datos_repedidos) == 1 and s.datos_repedidos[0].turno == 4


def test_mismo_rol_que_confirma_no_es_perdida():
    s = analizar(conv([
        ("agente", "¿Me regala su número de cédula?"), ("cliente", "1023456789"),
        ("agente", "Gracias. Ahora me regala su número de celular"), ("cliente", "3001234567"),
    ]))
    assert s.datos_repedidos == []


def test_trayectoria_desescalada():
    s = analizar(conv([
        ("cliente", "¡¡Llevo cinco días sin servicio, son unos ineptos!! Es la cuarta vez que llamo"),
        ("agente", "Tiene toda la razón, yo me encargo."),
        ("cliente", "Bueno"),
        ("agente", "Listo, ya quedó restablecido el servicio."),
        ("cliente", "Perfecto, muchas gracias"),
        ("cliente", "Muy amable"),
    ]))
    assert s.trayectoria == "desescalada"
    assert s.insultos_cliente and s.resolucion == "resuelto"


def test_trayectoria_escalada():
    s = analizar(conv([
        ("cliente", "Hola, quiero cancelar"),
        ("agente", "Antes de cancelar le ofrezco un descuento"),
        ("cliente", "No, gracias"),
        ("agente", "Le mejoro la oferta"),
        ("cliente", "Ya le dije que no, es la tercera vez que llamo, es el colmo"),
        ("cliente", "No sirve para nada este servicio"),
    ], tipo="cancelacion"))
    assert s.trayectoria == "escalada"
    assert s.retencion_antes_de_radicar is not None and s.retencion_antes_de_radicar.turno == 2


def test_resolucion_desmentida_por_cliente():
    s = analizar(conv([("agente", "Listo, ya quedó solucionado."), ("cliente", "Sigue igual, no me funciona")]))
    assert s.resolucion == "no_resuelto"


def test_en_tramite_con_radicado_y_plazo():
    s = analizar(conv([("cliente", "Quiero poner un reclamo por un cobro"),
                       ("agente", "Su radicado es 2026-0045871 y le respondemos en 15 días hábiles.")]))
    assert s.queja and s.radicado and s.plazo and s.resolucion == "en_tramite"


def test_pide_otp_y_negacion():
    s = analizar(conv([("agente", "Me dicta el código que le llegó al celular, por favor")]))
    assert s.pide_credencial
    s2 = analizar(conv([("agente", "Recuerde: nunca le pediremos su clave ni el código que le llegó.")]))
    assert not s2.pide_credencial


def test_tarjeta_expuesta():
    s = analizar(conv([("agente", "Su tarjeta es la 4111 1111 1111 1111")]))
    assert s.datos_expuestos


def test_coercion_cobranza():
    s = analizar(conv([("agente", "Si no paga hoy vamos a llamar a su familia y a su jefe")], tipo="cobranza"))
    assert s.coercion


def test_verificacion_antes_de_info():
    mal = analizar(conv([("agente", "Su saldo pendiente es de $480.000"), ("agente", "Para su seguridad, confirme su cédula")]))
    assert mal.verificacion_antes_de_info is False
    bien = analizar(conv([("agente", "Para su seguridad, confirme su cédula"), ("cliente", "1023456789"),
                          ("agente", "Su saldo pendiente es de $480.000")]))
    assert bien.verificacion_antes_de_info is True


def test_aceptacion_debil_no_cuenta():
    s = analizar(conv([("agente", "¿Le activo el plan de una vez, listo?"), ("cliente", "Bueno, ya, como sea")], tipo="ventas"))
    assert s.aceptacion is None
    s2 = analizar(conv([("agente", "¿Acepta la contratación del plan?"), ("cliente", "Sí, acepto")], tipo="ventas"))
    assert s2.aceptacion is not None


def test_temas():
    s = analizar(conv([("cliente", "No tengo internet y además me cobraron doble la factura")]))
    assert {"falla_tecnica", "facturacion", "cobro_no_reconocido"} <= set(s.temas)
