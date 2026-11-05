"""Conjunto ciego v4: escrito tras ajustar con v3. Se mide y se publica SIN ajustar después."""
import json
from pathlib import Path

C = []
def caso(id_, turnos, esperado, **kw):
    C.append({"id": id_, "turnos": [{"rol": r, "texto": t} for r, t in turnos], "esperado": esperado, **kw})

caso("a1", [("bot", "Hola 👋 soy Tobi, el asistente virtual"), ("cliente", "tobi no te ofendas pero prefiero hablar con gente"),
            ("bot", "¡Claro! Te comunico con nuestro equipo."), ("agente", "Hola, soy Fernanda del equipo de servicio.")],
     {"peticion_humano": True, "humano_atendido": True})
caso("a2", [("bot", "Escoge: 1 facturas 2 daños"), ("cliente", "quiero un asesor ya"), ("bot", "Escoge: 1 facturas 2 daños"),
            ("cliente", "asesor"), ("bot", "Escoge: 1 facturas 2 daños")], {"peticion_humano": True, "humano_atendido": False, "bucle": True})
caso("a3", [("bot", "Soy tu asistente virtual."), ("cliente", "la asesora del punto me dijo que llamara aquí para el cambio de plan"),
            ("bot", "Listo, ya cambié tu plan al de 20 GB. Se activa mañana."), ("cliente", "gracias")],
     {"peticion_humano": False, "resolucion": "resuelto"})
caso("b1", [("bot", "Cuál es tu número de contrato?"), ("cliente", "887766"), ("bot", "Gracias, ya te comunico con soporte técnico"),
            ("agente", "Soporte, buenos días. Necesito el número de contrato para revisar")], {"perdida_contexto": True})
caso("b2", [("bot", "Escribe tu cédula"), ("cliente", "1.110.222.333"), ("bot", "Te paso con una asesora"),
            ("agente", "Hola, ya veo tu información. ¿Qué inconveniente tienes con la tarjeta?")], {"perdida_contexto": False})
caso("c1", [("cliente", "no me dejan sacar plata del cajero"), ("agente", "Su tarjeta estaba bloqueada por intentos fallidos. Ya la desbloqueé, puede intentar."),
            ("cliente", "ya pude sacar, gracias")], {"resolucion": "resuelto"})
caso("c2", [("cliente", "el técnico no vino a la cita"), ("agente", "Qué pena con usted. No tengo agenda disponible esta semana."),
            ("cliente", "¿o sea que me quedo sin servicio?"), ("agente", "Toca esperar.")], {"resolucion": "no_resuelto"})
caso("c3", [("cliente", "necesito poner un reclamo por un daño en mi nevera después del corte de luz"),
            ("agente", "Claro. Radiqué su reclamación con el número RC-20261104; la respuesta llega en 15 días hábiles.")],
     {"resolucion": "en_tramite", "queja": True, "radicado": True})
caso("c4", [("cliente", "hola, ¿cuál es el horario de la oficina del centro?"), ("agente", "De lunes a viernes de 8 a 5."), ("cliente", "vale, gracias")],
     {"resolucion": "resuelto", "queja": False})
caso("d1", [("agente", "Para terminar la validación, necesito que me diga el PIN de la tarjeta")], {"credencial": True})
caso("d2", [("agente", "Recuerde que su clave es secreta: no la entregue a nadie.")], {"credencial": False})
caso("d3", [("agente", "Le acaba de llegar un mensaje de texto con 6 números, ¿me los puede leer?")], {"credencial": True})
caso("e1", [("agente", "Si no paga, mañana mismo llamamos a su empresa para informar a recursos humanos")], {"coercion": True}, tipo="cobranza")
caso("e2", [("agente", "Le enviamos al correo el estado de cuenta con las opciones de pago.")], {"coercion": False}, tipo="cobranza")
caso("f1", [("cliente", "cancelen la tarjeta de crédito"), ("agente", "Señora, antes de eso, ¿sabía que le podemos quitar la cuota de manejo?")],
     {"retencion": True}, tipo="cancelacion", sector="financiero")
caso("g1", [("agente", "¿Me confirma que acepta el plan con permanencia de 12 meses?"), ("cliente", "sí, confirmo")], {"aceptacion": True}, tipo="ventas")
caso("g2", [("agente", "¿Le hago la activación de una vez?"), ("cliente", "hmm no sé, déjeme pensarlo")], {"aceptacion": False}, tipo="ventas")
caso("h1", [("cliente", "les voy a poner una queja en la SIC por publicidad engañosa")], {"amenaza_externa": True})
caso("h2", [("cliente", "estoy averiguando si la tutela que puse ya salió, me dijeron que llamara acá")], {"amenaza_externa": True})
caso("h3", [("cliente", "¿me pueden enviar el paz y salvo para la notaría?")], {"amenaza_externa": False})
caso("i1", [("cliente", "buenas noches"), ("cliente", "necesito ayuda urgente con un fraude")], {"sin_respuesta": True})
caso("j1", [("cliente", "¡¡Me cobraron dos veces!! 😤"), ("agente", "Lamento mucho la molestia, ya mismo lo reviso."),
            ("agente", "Listo, ya le reversé el cobro duplicado."), ("cliente", "ok, mil gracias"), ("cliente", "muy amable")],
     {"trayectoria": "desescalada", "resolucion": "resuelto"})

Path(__file__).with_name("casos_v4_ciego.jsonl").write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in C) + "\n", encoding="utf-8")
print(len(C), "casos")
