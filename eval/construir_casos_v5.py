"""Conjunto ciego v5: escrito antes de la mejora de negaciones (revisión 5). Incluye trampas de negación."""
import json
from pathlib import Path

C = []


def caso(id_, turnos, esperado, **kw):
    C.append({"id": id_, "turnos": [{"rol": r, "texto": t} for r, t in turnos], "esperado": esperado, **kw})


caso("n1", [("bot", "Hola, soy el asistente virtual"), ("cliente", "no necesito un asesor, solo quiero saber mi saldo"),
            ("bot", "Tu saldo es $85.000.")], {"peticion_humano": False})
caso("n2", [("bot", "Soy el asistente digital"), ("cliente", "no me pase con nadie, usted me sirve"), ("bot", "Perfecto, cuéntame.")],
     {"peticion_humano": False})
caso("n3", [("bot", "¿En qué te ayudo?"), ("cliente", "sin asesor no voy a poder, páseme con alguien por favor"),
            ("bot", "Te comunico con un asesor."), ("agente", "Hola, habla Sergio.")], {"peticion_humano": True, "humano_atendido": True})
caso("n4", [("cliente", "no voy a poner ninguna queja en la superintendencia, tranquila"), ("agente", "Gracias por su comprensión")],
     {"amenaza_externa": False})
caso("n5", [("cliente", "si esto sigue así los voy a denunciar ante la SIC"), ("agente", "Entiendo")], {"amenaza_externa": True})
caso("n6", [("cliente", "no es urgente ni estoy molesta, solo quería confirmar la fecha"), ("agente", "Su pago vence el 20."),
            ("cliente", "listo, gracias")], {"resolucion": "resuelto", "trayectoria": "estable"})
caso("n7", [("cliente", "no quiero reclamar nada, solo saber cuándo llega la factura"), ("agente", "Llega el día 5 de cada mes.")],
     {"queja": False})
caso("n8", [("cliente", "quiero poner un reclamo porque no me llegó la devolución"),
            ("agente", "Le radiqué el reclamo con el número 45-998877; respuesta en 15 días hábiles.")],
     {"queja": True, "radicado": True, "resolucion": "en_tramite"})
caso("m1", [("agente", "Por seguridad no le voy a pedir su clave; solo confirme su fecha de nacimiento.")], {"credencial": False})
caso("m2", [("agente", "Para continuar necesito que me diga la contraseña de su correo")], {"credencial": True})
caso("m3", [("agente", "No vamos a llamar a su familia; le escribimos solo a usted.")], {"coercion": False}, tipo="cobranza")
caso("m4", [("agente", "Si no responde, le contamos a su esposa lo de la deuda")], {"coercion": True}, tipo="cobranza")
caso("m5", [("cliente", "quiero cancelar"), ("agente", "Listo, cancelación radicada con CUN 4411-22334455. No le voy a ofrecer nada más.")],
     {"retencion": False}, tipo="cancelacion", sector="telecom")
caso("m6", [("bot", "Escribe tu número de documento"), ("cliente", "80123456"), ("bot", "Te paso con una asesora"),
            ("agente", "Hola, ya tengo su documento, no se lo voy a volver a pedir. ¿Qué pasó con la compra?")], {"perdida_contexto": False})
caso("m7", [("agente", "¿Acepta el cambio de plan?"), ("cliente", "no, no acepto")], {"aceptacion": False}, tipo="ventas")
caso("m8", [("agente", "¿Me confirma que acepta?"), ("cliente", "sí, claro que acepto")], {"aceptacion": True}, tipo="ventas")

Path(__file__).with_name("casos_v5_ciego.jsonl").write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in C) + "\n", encoding="utf-8")
print(len(C), "casos")
