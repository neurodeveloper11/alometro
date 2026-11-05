"""Conjunto ciego v3: escrito tras la revisión 2 y ANTES de cualquier ajuste posterior.

Mezcla regiones (costeño, paisa, rolo), WhatsApp informal, errores de ortografía y trampas
de falsos positivos. Es la cifra honesta de la versión 0.1.
"""
import json
from pathlib import Path

C = []
def caso(id_, turnos, esperado, **kw):
    C.append({"id": id_, "turnos": [{"rol": r, "texto": t} for r, t in turnos], "esperado": esperado, **kw})

caso("p01", [("bot", "Hola, soy Ana, asistente digital del banco."), ("cliente", "ana pasame con un man de verdad q tu no entiendes"),
             ("bot", "Puedo ayudarte con: saldos, bloqueos, certificados."), ("cliente", "ya va, asesor humano!!!")],
     {"peticion_humano": True, "humano_atendido": False})
caso("p02", [("bot", "Bienvenido a la línea de atención."), ("cliente", "quisiera que me atendiera un funcionario"),
             ("bot", "Con gusto, te transfiero."), ("bot", "Estamos transfiriendo tu chat."), ("bot", "Sigues en la fila, en breve te atenderemos."),
             ("agente", "Hola, buenas, soy Liliana.")],
     {"peticion_humano": True, "humano_atendido": True})
caso("p03", [("bot", "¿En qué te ayudo?"), ("cliente", "la persona que me vendió el plan me dijo que no tenía permanencia"),
             ("bot", "Tu plan no tiene cláusula de permanencia."), ("cliente", "ah listo, era eso")],
     {"peticion_humano": False, "resolucion": "resuelto"})
caso("l01", [("bot", "Escribe tu consulta"), ("cliente", "cambio de titular"), ("bot", "No comprendo. Escribe tu consulta"),
             ("cliente", "cambiar el titular del servicio"), ("bot", "No comprendo. Escribe tu consulta")], {"bucle": True})
caso("l02", [("bot", "¿Deseas consultar tu saldo? Responde sí o no."), ("cliente", "sí"), ("bot", "Tu saldo es $120.500. ¿Algo más?"),
             ("cliente", "no gracias")], {"bucle": False, "resolucion": "resuelto"})
caso("x21", [("bot", "Indícame tu número de celular"), ("cliente", "3104445566"), ("bot", "Te paso con un agente"),
             ("agente", "Buenas, ¿desde qué número de celular me escribe?")], {"perdida_contexto": True})
caso("x22", [("agente", "¿Su correo electrónico?"), ("cliente", "lucho@mail.com"), ("agente", "Le confirmo que le llegó la factura a lucho@mail.com")],
     {"perdida_contexto": False})
caso("x23", [("bot", "Digita tu cédula"), ("cliente", "52.111.222"), ("bot", "Gracias"), ("bot", "Te transferimos al área de cartera"),
             ("agente", "Cartera. Antes de seguir, ¿me dicta su cédula?")], {"perdida_contexto": True})
caso("s21", [("cliente", "me están cobrando un servicio que cancelé hace dos meses"),
             ("agente", "Ya revisé y efectivamente quedó mal la cancelación. Le reverso los dos cobros y ya le quedó cancelado el servicio."),
             ("cliente", "bueno, gracias por la ayuda")], {"resolucion": "resuelto", "queja": True})
caso("s22", [("cliente", "llevo una semana sin luz en la casa"), ("agente", "Uy no, no tengo información de esa zona."),
             ("cliente", "¿y entonces?"), ("agente", "Intente llamar mañana.")], {"resolucion": "no_resuelto"})
caso("s23", [("cliente", "mi pedido no ha llegado"), ("agente", "Generé la solicitud de seguimiento #880021 con la transportadora; le responden en 24 horas hábiles."),
             ("cliente", "ok")], {"resolucion": "en_tramite", "radicado": True})
caso("s24", [("cliente", "necesito el certificado tributario"), ("agente", "Ya se lo envié al correo registrado."), ("cliente", "llegó, mil gracias")],
     {"resolucion": "resuelto"})
caso("s25", [("cliente", "quiero hacer un reclamo formal por mal servicio"), ("agente", "Listo"), ("cliente", "¿y el número del reclamo?"),
             ("agente", "Eso le llega después.")], {"queja": True, "radicado": False})
caso("c21", [("agente", "Dígame la clave que usa para el cajero y se la cambio")], {"credencial": True})
caso("c22", [("agente", "Le enviamos un código. Ese código es personal: ningún funcionario se lo va a pedir.")], {"credencial": False})
caso("c23", [("agente", "Para validar, léame el token que le aparece en la app")], {"credencial": True})
caso("k21", [("agente", "Mire, si no paga hoy le cae la policía")], {"coercion": True}, tipo="cobranza")
caso("k22", [("agente", "Le informo que su obligación tiene 40 días de mora. ¿Podemos acordar una fecha de pago?")], {"coercion": False}, tipo="cobranza")
caso("k23", [("agente", "Ya le dejamos razón con su vecina para que nos devuelva la llamada")], {"coercion": True}, tipo="cobranza")
caso("r21", [("cliente", "voy a cancelar el internet"), ("agente", "¿Y si le doblamos la velocidad gratis por tres meses?")],
     {"retencion": True}, tipo="cancelacion", sector="telecom")
caso("r22", [("cliente", "cancelen mi seguro"), ("agente", "Listo, quedó radicada la cancelación del seguro con el número 2026-55110.")],
     {"retencion": False, "radicado": True}, tipo="cancelacion", sector="seguros")
caso("v21", [("agente", "¿Acepta las condiciones del crédito que le acabo de leer?"), ("cliente", "sí, las acepto")], {"aceptacion": True}, tipo="ventas")
caso("v22", [("agente", "¿Entonces se lo activo?"), ("cliente", "mándeme la información por correo y yo miro")], {"aceptacion": False}, tipo="ventas")
caso("v23", [("agente", "¿Autoriza que le carguemos el seguro a la tarjeta?"), ("cliente", "bueno, si toca")], {"aceptacion": False}, tipo="ventas")
caso("t21", [("cliente", "Me van a tener que responder o los demando, ya hablé con un abogado")], {"amenaza_externa": True})
caso("t22", [("cliente", "trabajo en la superintendencia de sociedades y necesito un certificado")], {"amenaza_externa": False})
caso("t23", [("cliente", "voy a poner esto en twitter, son unos sinvergüenzas")], {"amenaza_externa": True})
caso("n01", [("cliente", "buenas, alguien?"), ("cliente", "hola??")], {"sin_respuesta": True})
caso("n02", [("cliente", "hola"), ("bot", "Hola, ¿en qué te ayudo?")], {"sin_respuesta": False})
caso("e01", [("cliente", "¡Esto es el colmo! Tres días sin internet 😡"), ("agente", "Tiene toda la razón, lo siento mucho. Ya encontré la falla y la estoy corrigiendo."),
             ("cliente", "bueno"), ("agente", "Listo, ya quedó restablecido."), ("cliente", "sí, ya volvió. Gracias, muy amable"), ("cliente", "que tenga buen día")],
     {"trayectoria": "desescalada", "resolucion": "resuelto"})
caso("e02", [("cliente", "hola, quiero saber por qué subió la factura"), ("agente", "Es por el reajuste anual."), ("cliente", "¿y por qué nadie avisó?"),
             ("agente", "Es política de la empresa."), ("cliente", "qué falta de respeto, llevo diez años con ustedes"), ("cliente", "me voy para la competencia")],
     {"trayectoria": "escalada"})

Path(__file__).with_name("casos_v3_ciego.jsonl").write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in C) + "\n", encoding="utf-8")
print(len(C), "casos")
