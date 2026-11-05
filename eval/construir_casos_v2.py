"""Conjunto ciego v2: escrito DESPUÉS de ajustar con v1 y ANTES de volver a tocar el motor.

Redacciones nuevas (regionalismos, errores de tipeo, sin tildes, mensajes cortos de WhatsApp).
Las cifras sobre este conjunto son la estimación honesta de la versión 0.1.
"""
import json
from pathlib import Path

C = []
def caso(id_, turnos, esperado, **kw):
    C.append({"id": id_, "turnos": [{"rol": r, "texto": t} for r, t in turnos], "esperado": esperado, **kw})

caso("b01", [("bot", "Hola, soy Juli, tu asistente virtual. ¿En qué te ayudo hoy?"), ("cliente", "necesito q me atienda una persona x favor"),
             ("bot", "¡Claro! Para eso necesito que me digas tu consulta."), ("cliente", "persona!!"),
             ("bot", "¡Claro! Para eso necesito que me digas tu consulta.")],
     {"peticion_humano": True, "humano_atendido": False, "bucle": True}, canal="whatsapp")
caso("b02", [("bot", "Hola 👋 ¿Cómo te puedo ayudar?"), ("cliente", "hablar con asesor"),
             ("bot", "Te estoy transfiriendo con un asesor."), ("agente", "Hola, bienvenido, soy Mateo.")],
     {"peticion_humano": True, "humano_atendido": True, "bucle": False})
caso("b03", [("bot", "Soy tu asistente automático."), ("cliente", "mi asesora comercial se llama Patricia, quiero saber si ya radicó mi crédito"),
             ("bot", "Tu solicitud de crédito está en estudio. Te avisaremos por correo en máximo 3 días hábiles."), ("cliente", "vale gracias")],
     {"peticion_humano": False, "resolucion": "resuelto"})
caso("b04", [("bot", "Elige una opción: 1) Pagos 2) Daños 3) Otros"), ("cliente", "3"), ("bot", "Elige una opción: 1) Pagos 2) Daños 3) Otros"),
             ("cliente", "3"), ("bot", "Elige una opción: 1) Pagos 2) Daños 3) Otros")],
     {"bucle": True, "peticion_humano": False})
caso("b05", [("bot", "Hola, ¿en que te ayudo?"), ("cliente", "no me contesta ni un robot ni nadie, comuniqueme con un funcionario"),
             ("bot", "Nuestros horarios de atención son de 7 a 7."), ("cliente", "...")],
     {"peticion_humano": True, "humano_atendido": False})
caso("c11", [("bot", "Por favor ingresa tu número de póliza"), ("cliente", "POL-883311"), ("bot", "Gracias, te comunico con un asesor."),
             ("agente", "Buenos días, me indica por favor el número de póliza?")], {"perdida_contexto": True})
caso("c12", [("bot", "¿Cuál es tu nombre completo?"), ("cliente", "Ana María Rodríguez"), ("bot", "Te paso con una persona."),
             ("agente", "Hola Ana María, ¿me confirma su número de celular para devolverle la llamada si se corta?")], {"perdida_contexto": False})
caso("c13", [("agente", "Me regala su cédula?"), ("cliente", "79.555.444"), ("agente", "Lo comunico con el área de cartera."),
             ("agente", "Cartera, buenas tardes. Su número de documento por favor")], {"perdida_contexto": True})
caso("r11", [("cliente", "no me llega el codigo para entrar a la app"), ("agente", "Le reenvié el código, revise por favor."),
             ("cliente", "ya me llegó y ya entré, gracias")], {"resolucion": "resuelto"})
caso("r12", [("cliente", "el medidor está dañado y me están cobrando de más"), ("agente", "Eso lo debe solicitar por la página web."),
             ("cliente", "pero no me deja la página")], {"resolucion": "no_resuelto"})
caso("r13", [("cliente", "quiero poner una queja por mal servicio del técnico"),
             ("agente", "Claro, le tomo la queja. Su número de PQR es 2026-778899 y le respondemos en un plazo de 15 días hábiles.")],
     {"resolucion": "en_tramite", "queja": True, "radicado": True})
caso("r14", [("cliente", "me cobraron la cuota de manejo y me dijeron que era gratis"), ("agente", "Ya le hice el reverso de la cuota de manejo, se refleja en 48 horas."),
             ("cliente", "ah bueno, muchas gracias")], {"resolucion": "resuelto", "queja": True})
caso("r15", [("cliente", "no tengo agua desde ayer"), ("agente", "Estamos en mantenimiento en el sector, el servicio vuelve hoy a las 6 p. m."),
             ("cliente", "ok")], {"resolucion": "resuelto"})
caso("r16", [("cliente", "el pedido llegó incompleto"), ("agente", "Ese tema no lo manejo yo, comuníquese con la transportadora."),
             ("cliente", "y el número?"), ("agente", "No lo tengo.")], {"resolucion": "no_resuelto"})
caso("s11", [("agente", "Para continuar, escríbame el código de 6 dígitos que le acaba de llegar por SMS")], {"credencial": True})
caso("s12", [("agente", "¿Me confirma el número completo de su tarjeta y la fecha de vencimiento?")], {"credencial": True})
caso("s13", [("agente", "Por su seguridad, nunca comparta su clave dinámica con nadie.")], {"credencial": False})
caso("k11", [("agente", "Le informo que si no paga, el lunes pasamos por su casa a cobrar personalmente")], {"coercion": True}, tipo="cobranza")
caso("k12", [("agente", "Podemos ofrecerle un acuerdo de pago a 6 cuotas, ¿le parece?")], {"coercion": False}, tipo="cobranza")
caso("k13", [("agente", "Si no paga, vamos a llamar a las referencias que dejó en el crédito")], {"coercion": True}, tipo="cobranza")
caso("x11", [("cliente", "deseo cancelar la suscripción"), ("agente", "Lamento escuchar eso. ¿Le gustaría recibir un mes gratis para que lo piense?"),
             ("cliente", "no")], {"retencion": True}, tipo="cancelacion", sector="telecom")
caso("x12", [("cliente", "quiero cancelar el plan"), ("agente", "Con gusto, ¿me confirma su cédula?"), ("cliente", "1.098.765.432"),
             ("agente", "Listo, cancelación radicada, CUN 4455-66778899, le llega al correo.")],
     {"retencion": False, "radicado": True}, tipo="cancelacion", sector="telecom")
caso("v11", [("agente", "Entonces, ¿le confirmo la compra del seguro de vida por $35.000 mensuales?"), ("cliente", "sí, hágale")],
     {"aceptacion": True}, tipo="ventas")
caso("v12", [("agente", "¿Autoriza el débito automático?"), ("cliente", "pues si toca")], {"aceptacion": False}, tipo="ventas")
caso("v13", [("agente", "¿Está de acuerdo con activar el plan?"), ("cliente", "No señor, gracias")], {"aceptacion": False}, tipo="ventas")
caso("a11", [("cliente", "esto lo voy a subir a tiktok para que la gente vea como tratan a los clientes")], {"amenaza_externa": True})
caso("a12", [("cliente", "me voy a quejar ante la super")], {"amenaza_externa": True})
caso("a13", [("cliente", "quiero cambiar la dirección de facebook de mi negocio en el directorio")], {"amenaza_externa": False})
caso("a14", [("cliente", "mi abogado me pidió el certificado de deuda")], {"amenaza_externa": False})

Path(__file__).with_name("casos_v2_ciego.jsonl").write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in C) + "\n", encoding="utf-8")
print(len(C), "casos")
