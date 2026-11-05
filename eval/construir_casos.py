"""Conjunto de evaluación v1 escrito a mano, con redacciones distintas a las del generador sintético.

Se escribió ANTES de ajustar los léxicos a estos casos. Las etiquetas son el juicio del autor.
Es pequeño: sirve para detectar regresiones y huecos, no como cifra definitiva.
"""
import json
from pathlib import Path

C = []
def caso(id_, turnos, esperado, **kw):
    C.append({"id": id_, "turnos": [{"rol": r, "texto": t} for r, t in turnos], "esperado": esperado, **kw})

# --- Petición de humano / bot ---
caso("h01", [("bot", "Hola! Soy Sofi 🤖 ¿qué necesitas?"), ("cliente", "me puede comunicar con alguien de carne y hueso?"),
             ("bot", "Puedo ayudarte con pagos, saldo y certificados."), ("cliente", "operador por favor"),
             ("bot", "Puedo ayudarte con pagos, saldo y certificados.")],
     {"peticion_humano": True, "humano_atendido": False, "bucle": True}, canal="whatsapp")
caso("h02", [("bot", "Bienvenido. Para facturas marque 1, para soporte marque 2."), ("cliente", "0"),
             ("bot", "Opción inválida. Para facturas marque 1, para soporte marque 2."), ("cliente", "quiero un agente"),
             ("bot", "En un momento uno de nuestros asesores te atenderá."), ("agente", "Buenas tardes, habla Camilo, ¿en qué le colaboro?")],
     {"peticion_humano": True, "humano_atendido": True, "bucle": False})
caso("h03", [("bot", "Soy el asistente digital de la EPS."), ("cliente", "el asesor de ayer me dijo que ya estaba la autorización"),
             ("bot", "Déjame consultar. Tu autorización está aprobada y la puedes descargar en la app."), ("cliente", "listo, gracias")],
     {"peticion_humano": False, "bucle": False, "resolucion": "resuelto"})
caso("h04", [("bot", "Hola, ¿en qué te ayudo?"), ("cliente", "necesito hablar con una persona, el bot no me entiende"),
             ("bot", "No entendí tu pregunta. ¿Puedes reformularla?"), ("cliente", "PERSONA"),
             ("bot", "No entendí tu pregunta. ¿Puedes reformularla?"), ("cliente", "qué pereza, mejor me cambio de banco")],
     {"peticion_humano": True, "humano_atendido": False, "bucle": True, "resolucion": "no_resuelto"})
caso("h05", [("bot", "Hola, soy un asistente virtual. Escribe tu consulta."), ("cliente", "me pasa con un humano?"),
             ("bot", "Te transfiero con un asesor humano, un momento."), ("agente", "Hola, soy Diana. Veo que necesitas ayuda con tu pedido.")],
     {"peticion_humano": True, "humano_atendido": True, "bucle": False})
caso("h06", [("bot", "¡Hola! Te ayudo con tu pedido."), ("cliente", "no quiero hablar con una máquina"),
             ("bot", "Entiendo. ¿Me das tu número de pedido para ayudarte?"), ("cliente", "...")],
     {"peticion_humano": True, "humano_atendido": False, "bucle": False})
# --- Pérdida de contexto ---
caso("c01", [("bot", "Digita tu número de documento sin puntos."), ("cliente", "1144098765"),
             ("bot", "Gracias, te paso con un especialista."), ("agente", "Hola, ¿cuál es su cédula?")],
     {"perdida_contexto": True})
caso("c02", [("bot", "¿Cuál es tu correo electrónico?"), ("cliente", "pepito.perez@correo.com"),
             ("bot", "Te paso con un asesor."), ("agente", "Hola Pepito, ya tengo tu correo, cuéntame qué pasó con el envío.")],
     {"perdida_contexto": False})
caso("c03", [("agente", "Me indica el número de contrato?"), ("cliente", "es el 556677"),
             ("agente", "Le voy a transferir al área de facturación."), ("agente", "Facturación, buenas. Me confirma el número de contrato?")],
     {"perdida_contexto": True})
# --- Resolución ---
caso("r01", [("cliente", "La app no me deja hacer transferencias"), ("agente", "Ya revisé, era un bloqueo preventivo. Ya lo levanté, intente de nuevo."),
             ("cliente", "ya pude, mil gracias")], {"resolucion": "resuelto"})
caso("r02", [("cliente", "No me ha llegado el reembolso"), ("agente", "Eso se demora, tiene que esperar."),
             ("cliente", "¿y cuánto? ya van dos meses"), ("agente", "No le sé decir.")], {"resolucion": "no_resuelto", "queja": True})
caso("r03", [("cliente", "Quiero reclamar por un cobro de seguro que no pedí"),
             ("agente", "Quedó registrada su solicitud con el número 7781-2026. Le damos respuesta en 8 días hábiles al correo.")],
     {"resolucion": "en_tramite", "queja": True, "radicado": True})
caso("r04", [("cliente", "¿A qué hora abren el sábado?"), ("agente", "Los sábados abrimos de 8 a 12."), ("cliente", "Ok gracias")],
     {"resolucion": "resuelto"})
caso("r05", [("cliente", "el internet está lentísimo"), ("agente", "Reiniciamos el equipo, ya debería funcionar bien."),
             ("cliente", "no, sigue lentísimo, esto es una burla")], {"resolucion": "no_resuelto"})
caso("r06", [("cliente", "tengo un problema con mi factura"), ("agente", "Debe escribir a nuestro correo de facturación."),
             ("cliente", "bueno")], {"resolucion": "no_resuelto"})
# --- Seguridad, cobranza, cancelación, ventas ---
caso("s01", [("agente", "Para validar su identidad dígame los 3 números de atrás de la tarjeta")], {"credencial": True})
caso("s02", [("agente", "Le llegó un mensaje con un código. NO lo comparta con nadie, ni siquiera con nosotros.")], {"credencial": False})
caso("s03", [("agente", "Señora, regáleme la contraseña de la banca virtual para revisarle")], {"credencial": True})
caso("k01", [("agente", "Si no se pone al día, le vamos a mandar un cobrador a la oficina donde trabaja")], {"coercion": True}, tipo="cobranza")
caso("k02", [("agente", "Le recuerdo que si persiste la mora se reporta a centrales de riesgo, previa notificación por escrito.")],
     {"coercion": False}, tipo="cobranza")
caso("k03", [("agente", "Ya hablamos con su mamá y le contamos que usted debe")], {"coercion": True}, tipo="cobranza")
caso("x01", [("cliente", "Quiero dar de baja la línea"), ("agente", "Claro, pero antes déjeme contarle que tenemos un plan con 30 % menos"),
             ("cliente", "no gracias")], {"retencion": True}, tipo="cancelacion", sector="telecom")
caso("x02", [("cliente", "Quiero cancelar el servicio de televisión"), ("agente", "Listo, su solicitud de cancelación quedó radicada con el CUN 4321-55667788.")],
     {"retencion": False, "radicado": True}, tipo="cancelacion", sector="telecom")
caso("v01", [("agente", "¿Está de acuerdo con las condiciones y autoriza la compra?"), ("cliente", "Sí señora, de acuerdo")],
     {"aceptacion": True}, tipo="ventas")
caso("v02", [("agente", "¿Le dejo activo el seguro entonces?"), ("cliente", "ay no sé, bueno pues")], {"aceptacion": False}, tipo="ventas")
caso("v03", [("agente", "¿Confirma que desea adquirir el plan?"), ("cliente", "no, déjeme lo consulto con mi esposo")],
     {"aceptacion": False}, tipo="ventas")
# --- Amenaza externa / emoción ---
caso("a01", [("cliente", "Si no me solucionan hoy los denuncio ante la Superintendencia de Industria y Comercio")], {"amenaza_externa": True})
caso("a02", [("cliente", "Vi en Instagram una promoción, ¿todavía está vigente?")], {"amenaza_externa": False})
caso("a03", [("cliente", "voy a interponer una acción de tutela porque esto es inhumano")], {"amenaza_externa": True})
caso("a04", [("cliente", "Hola, quería saber el saldo de mi cuenta")], {"amenaza_externa": False, "queja": False})

Path(__file__).with_name("casos_v1.jsonl").write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in C) + "\n", encoding="utf-8")
print(len(C), "casos")
