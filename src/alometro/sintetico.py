"""Generador de conversaciones sintéticas (español de Colombia) para demos y pruebas.

Todas las empresas, personas y números son ficticios. Los escenarios reproducen
los problemas más reportados en Colombia: bots en bucle que no pasan a una
persona, traspasos que piden de nuevo la cédula, cancelaciones con trabas,
ventas insistentes, cobranza fuera de horario y peticiones de claves.

`periodo="antes"` simula una operación típica; `periodo="despues"` la misma
operación tras aplicar las recomendaciones (para demostrar `alometro comparar`).
"""

from __future__ import annotations

import random
from collections.abc import Callable
from datetime import datetime, timedelta

from .calendario import HORA_COLOMBIA, es_festivo
from .modelos import Conversacion, Turno

AGENTES = ["Laura", "Andrés", "Valentina", "Jhon", "Daniela", "Carlos", "Paola", "Sebastián"]
CLIENTES = ["María", "José", "Luz Dary", "Jorge", "Yesenia", "Wilson", "Diana", "Fabián", "Marleny", "Óscar"]
EMPRESA = {"telecom": "ConectaYa", "financiero": "Banco Cordillera", "servicios_publicos": "Aguas y Luz del Valle",
           "comercio": "Tienda Pacífico", "salud": "Salud Vital", "general": "ServiTotal"}

T = tuple[str, str]  # (rol, texto)


def _ced(r: random.Random) -> str:
    return f"{r.randint(10, 1199)}.{r.randint(100, 999)}.{r.randint(100, 999)}"


def _cel(r: random.Random) -> str:
    return f"3{r.randint(0, 2)}{r.randint(0, 9)} {r.randint(100, 999)} {r.randint(1000, 9999)}"


def _rad(r: random.Random) -> str:
    return f"{r.randint(10, 99)}-{r.randint(10**9, 10**10 - 1)}"


# ----------------------------------------------------------------------------
# Escenarios: cada uno devuelve (tipo, canal, sector, direccion, turnos)
# ----------------------------------------------------------------------------
def servicio_ejemplar(r, v):
    return "soporte", "voz", "telecom", "entrante", [
        ("sistema", "Esta llamada puede ser grabada y monitoreada para fines de calidad."),
        ("agente", f"Buenas tardes, gracias por comunicarse con {EMPRESA['telecom']}, le habla {v['ag']}. ¿En qué le puedo ayudar?"),
        ("cliente", "Hola, no tengo internet desde ayer en la tarde y trabajo desde la casa."),
        ("agente", f"Entiendo su preocupación, {v['cli']}, quedarse sin internet trabajando desde casa es complicado. Para su seguridad, ¿me confirma su número de cédula?"),
        ("cliente", f"Sí, {v['ced']}."),
        ("agente", "Gracias. Si le entiendo bien, el servicio se cayó ayer en la tarde y desde entonces no conecta. Déjeme revisar el estado del módem."),
        ("cliente", "Exacto, la luz roja del módem está prendida."),
        ("agente", "Veo una falla en la configuración de su equipo. Voy a reiniciarlo de forma remota, me regala un momento."),
        ("agente", "Listo, acabo de restablecer la configuración. ¿Me confirma si ya le aparece la luz verde?"),
        ("cliente", "Sí, ya me funciona. ¡Qué bien!"),
        ("agente", "Perfecto. Le confirmo: reiniciamos y restablecimos la configuración del módem y el servicio quedó restablecido. ¿Hay algo más en lo que le pueda ayudar?"),
        ("cliente", "No, eso era todo. Muchas gracias."),
        ("agente", "Con gusto, que tenga una excelente tarde."),
    ]


def bot_bucle_sin_humano(r, v):
    sector = r.choice(["telecom", "financiero"])
    return "servicio", "whatsapp", sector, "entrante", [
        ("bot", f"¡Hola! Bienvenido a {EMPRESA[sector]}. Escribe el número de la opción: 1. Facturas 2. Planes 3. Soporte"),
        ("cliente", "Me cobraron doble la factura de este mes y necesito que me devuelvan la plata"),
        ("bot", "Lo siento, no te entendí. Escribe el número de la opción: 1. Facturas 2. Planes 3. Soporte"),
        ("cliente", "1"),
        ("bot", "Puedes descargar tu factura en nuestra app o página web. ¿Te puedo ayudar en algo más?"),
        ("cliente", "No quiero la factura, quiero hablar con un asesor"),
        ("bot", "Lo siento, no te entendí. Escribe el número de la opción: 1. Facturas 2. Planes 3. Soporte"),
        ("cliente", "ASESOR!!! QUIERO HABLAR CON UNA PERSONA"),
        ("bot", "Puedes descargar tu factura en nuestra app o página web. ¿Te puedo ayudar en algo más?"),
        ("cliente", "Esto no sirve para nada, voy a poner la queja en la Superintendencia"),
    ]


def bot_a_persona_sin_contexto(r, v):
    return "servicio", "chat", "financiero", "entrante", [
        ("bot", f"Hola, soy Cori, la asistente virtual de {EMPRESA['financiero']}. ¿En qué te puedo ayudar?"),
        ("cliente", "Tengo un cobro en la tarjeta que no reconozco, de una tienda en línea"),
        ("bot", "Para ayudarte, por favor escribe tu número de cédula."),
        ("cliente", v["ced"]),
        ("bot", "Gracias. Te voy a comunicar con un asesor del área de fraude."),
        ("agente", f"Buenas tardes, mi nombre es {v['ag']}. Por favor me regala su número de cédula."),
        ("cliente", "Ya se la di al bot hace un minuto, otra vez??"),
        ("agente", "Es necesario para validar la información."),
        ("cliente", v["ced"]),
        ("agente", "Gracias. Voy a bloquear la tarjeta y radicar la reclamación. Su número de caso es " + v["rad"] + " y tendrá respuesta en máximo 15 días hábiles."),
        ("cliente", "Bueno, gracias."),
        ("agente", "Con gusto, que tenga un buen día."),
    ]


def bot_a_persona_con_contexto(r, v):
    return "servicio", "chat", "financiero", "entrante", [
        ("bot", f"Hola, soy Cori, la asistente virtual de {EMPRESA['financiero']}. Si en algún momento prefieres hablar con un asesor, escribe «asesor»."),
        ("cliente", "Tengo un cobro en la tarjeta que no reconozco"),
        ("bot", "Para ayudarte, por favor escribe tu número de cédula."),
        ("cliente", v["ced"]),
        ("bot", "Gracias. Como es un posible fraude, te comunico con un asesor del área de fraude y le comparto lo que me contaste."),
        ("agente", f"Hola {v['cli']}, le habla {v['ag']}. Ya tengo su información: veo que reporta un cobro no reconocido de una tienda en línea. Lamento mucho la situación, yo me encargo."),
        ("cliente", "Gracias, sí, fue ayer por la noche."),
        ("agente", "Voy a bloquear la tarjeta ya mismo para que no haya más cobros. Listo, la tarjeta quedó bloqueada. Además radiqué la reclamación con el número de caso " + v["rad"] + "; la respuesta llega en máximo 15 días hábiles. Le recuerdo que nunca le pediremos claves ni códigos."),
        ("cliente", "Perfecto, muchas gracias."),
        ("agente", "Le confirmo entonces: tarjeta bloqueada y reclamación radicada. ¿Hay algo más en lo que le pueda ayudar?"),
        ("cliente", "No, eso es todo."),
        ("agente", "Que tenga un excelente día."),
    ]


def bot_resuelve(r, v):
    return "servicio", "whatsapp", "comercio", "entrante", [
        ("bot", f"¡Hola! Soy el asistente virtual de {EMPRESA['comercio']}. ¿En qué te puedo ayudar? Si prefieres una persona, escribe «asesor»."),
        ("cliente", "Hola, ¿cuándo llega mi pedido? Lo compré el lunes"),
        ("bot", "Claro. Escríbeme tu número de pedido, por favor."),
        ("cliente", f"PED-{r.randint(100000, 999999)}"),
        ("bot", "Tu pedido salió hoy con la transportadora y llega mañana entre 8:00 a. m. y 6:00 p. m. Te enviamos la guía a tu correo. ¿Algo más en lo que te pueda ayudar?"),
        ("cliente", "Perfecto, gracias"),
        ("bot", "¡Con gusto! Que tengas un buen día."),
    ]


def bot_pide_humano_atendido(r, v):
    sector = r.choice(["telecom", "servicios_publicos"])
    return "servicio", "whatsapp", sector, "entrante", [
        ("bot", f"Hola, soy el asistente virtual de {EMPRESA[sector]}. Cuéntame en qué te ayudo; si prefieres una persona, escribe «asesor»."),
        ("cliente", "Quiero hablar con un asesor, es sobre un cobro de reconexión que no entiendo"),
        ("bot", "Claro, te comunico con un asesor. Ya le compartí tu consulta sobre el cobro de reconexión."),
        ("agente", f"Hola, te habla {v['ag']}. Ya veo que tu consulta es por el cobro de reconexión. ¿Me confirmas tu número de cédula para revisarlo?"),
        ("cliente", v["ced"]),
        ("agente", "Gracias. El cobro se generó por un pago tardío, pero veo que pagaste a tiempo por otro canal. Voy a reversarlo. Listo, el cobro ya quedó reversado y se refleja en la próxima factura."),
        ("cliente", "Excelente, muchas gracias"),
        ("agente", "Te confirmo: cobro de reconexión reversado. ¿Hay algo más en lo que te pueda ayudar?"),
        ("cliente", "No, eso es todo"),
        ("agente", "Que tengas un buen día."),
    ]


def queja_radicada(r, v):
    return "servicio", "voz", "servicios_publicos", "entrante", [
        ("sistema", "Le informamos que esta llamada será grabada para fines de calidad."),
        ("agente", f"Buenos días, le habla {v['ag']} de {EMPRESA['servicios_publicos']}. ¿En qué le puedo colaborar?"),
        ("cliente", "La factura me llegó por el triple, yo vivo sola y no gasto esa cantidad de agua. Quiero poner un reclamo."),
        ("agente", "Comprendo su molestia, un cobro así preocupa a cualquiera. Para su seguridad, ¿me confirma su número de cédula?"),
        ("cliente", f"Claro, {v['ced']}."),
        ("agente", "Gracias. Entonces usted me dice que el consumo facturado no corresponde a lo que gasta normalmente. Voy a radicar el reclamo y a programar una revisión del medidor."),
        ("cliente", "Sí, eso."),
        ("agente", f"Listo. Su número de radicado es {v['rad']}. Tenemos 15 días hábiles para responderle y la visita técnica queda programada para el jueves. Mientras tanto no tiene que pagar el valor en reclamo."),
        ("cliente", "Bueno, muy amable."),
        ("agente", "Le confirmo: reclamo radicado, visita el jueves y respuesta en máximo 15 días hábiles. ¿Alguna otra inquietud?"),
        ("cliente", "No, gracias."),
        ("agente", "Que tenga un feliz día."),
    ]


def agente_evasivo(r, v):
    return "servicio", "voz", "salud", "entrante", [
        ("agente", f"{EMPRESA['salud']}, buenas."),
        ("cliente", "Buenas, llevo tres semanas esperando la autorización de un examen y nadie me da razón."),
        ("agente", "Eso no es conmigo, eso lo maneja otra área."),
        ("cliente", "¿Y entonces con quién? Ya les dije la vez pasada lo mismo."),
        ("agente", "Tiene que acercarse a una oficina con la orden médica."),
        ("cliente", "Pero yo no puedo ir, estoy enferma, por eso llamo."),
        ("agente", "No se puede hacer por teléfono. Es política de la empresa."),
        ("cliente", "O sea que no me van a solucionar nada. Voy a poner una tutela, es el colmo."),
        ("agente", "Bueno, hasta luego."),
    ]


def cancelacion_con_retencion(r, v):
    return "cancelacion", "voz", "telecom", "entrante", [
        ("sistema", "Esta llamada puede ser grabada y monitoreada."),
        ("agente", f"Buenas tardes, le habla {v['ag']} de {EMPRESA['telecom']}. ¿En qué le puedo ayudar?"),
        ("cliente", "Quiero cancelar mi plan de celular, por favor."),
        ("agente", "Antes de cancelar, le puedo ofrecer un descuento del 50 % por seis meses."),
        ("cliente", "No, gracias, ya lo decidí. Quiero cancelar."),
        ("agente", "Le mejoro la oferta: le dejo el plan con el doble de datos al mismo precio. ¿Por qué no lo piensa?"),
        ("cliente", "Ya le dije que no. Es la tercera vez que llamo para esto, me tienen cansado."),
        ("agente", "Bueno. Le radico la solicitud."),
        ("cliente", "Gracias."),
    ]


def cancelacion_correcta(r, v):
    return "cancelacion", "chat", "telecom", "entrante", [
        ("agente", f"Hola, te habla {v['ag']} del canal de cancelación de {EMPRESA['telecom']}. ¿Qué servicio quieres cancelar?"),
        ("cliente", "La línea móvil postpago, por favor."),
        ("agente", "Claro. Por tu seguridad, ¿me confirmas tu número de cédula?"),
        ("cliente", v["ced"]),
        ("agente", f"Gracias. Listo, ya quedó radicada la cancelación con el CUN {v['rad']}. Te enviamos el CUN a tu correo y la línea queda cancelada al cierre del ciclo de facturación."),
        ("cliente", "Perfecto, gracias."),
        ("agente", "Te confirmo: cancelación radicada y CUN enviado a tu correo. ¿Algo más en lo que te pueda ayudar?"),
        ("cliente", "No, eso es todo."),
        ("agente", "Que tengas una excelente tarde."),
    ]


def venta_correcta(r, v):
    return "ventas", "voz", "telecom", "saliente", [
        ("agente", f"Buenos días, le habla {v['ag']} de {EMPRESA['telecom']}. Esta llamada está siendo grabada para fines de calidad. ¿Hablo con {v['cli']}?"),
        ("cliente", "Sí, con ella."),
        ("agente", "La llamo porque tiene disponible un plan de internet de 500 megas. ¿Tiene un minuto para contarle?"),
        ("cliente", "Bueno, cuénteme."),
        ("agente", "¿Cuántas personas usan el internet en su casa y para qué lo usan principalmente?"),
        ("cliente", "Somos cuatro, los niños estudian y yo trabajo desde la casa."),
        ("agente", "Entonces le sirve un plan con más velocidad. El plan cuesta $95.000 al mes los primeros seis meses y después $115.000. Tiene permanencia de 12 meses; si cancela antes hay una cláusula de $80.000."),
        ("cliente", "Me interesa."),
        ("agente", "Para registrar la solicitud necesito sus datos. ¿Autoriza el tratamiento de sus datos personales según nuestra política de tratamiento de datos?"),
        ("cliente", "Sí, autorizo."),
        ("agente", "Gracias. ¿Me confirma su número de cédula?"),
        ("cliente", v["ced"]),
        ("agente", "Le recuerdo que tiene derecho de retracto: cinco días hábiles para arrepentirse sin costo. ¿Acepta la contratación del plan en estas condiciones?"),
        ("cliente", "Sí, acepto."),
        ("agente", "Listo, su solicitud quedó registrada y la instalación queda programada para el sábado. Le confirmo: plan de 500 megas, $95.000 los primeros seis meses y permanencia de 12 meses. ¿Algo más en lo que le pueda ayudar?"),
        ("cliente", "No, gracias."),
        ("agente", "Que tenga un excelente día."),
    ]


def venta_agresiva(r, v):
    return "ventas", "voz", "telecom", "saliente", [
        ("agente", f"Hola, le hablo de {EMPRESA['telecom']}, tenemos una promoción solo por hoy."),
        ("cliente", "No me interesa, gracias."),
        ("agente", "Pero es la última oportunidad, le regalamos tres meses gratis de televisión."),
        ("cliente", "Le dije que no me interesa. ¿Por qué me llaman a esta hora?"),
        ("agente", "Le dejo el plan con descuento, es un beneficio exclusivo. Le activo el plan de una vez, ¿listo?"),
        ("cliente", "Bueno, ya, como sea."),
        ("agente", "Perfecto, bienvenido a la familia " + EMPRESA["telecom"] + ", su plan quedó activo."),
    ]


def cobranza_respetuosa(r, v):
    return "cobranza", "voz", "financiero", "saliente", [
        ("agente", f"Buenos días, le habla {v['ag']} de {EMPRESA['financiero']}. Esta llamada está siendo grabada. ¿Hablo con {v['cli']}?"),
        ("cliente", "Sí, con él."),
        ("agente", "Para su seguridad, ¿me confirma la fecha de expedición de su cédula?"),
        ("cliente", "El 3 de marzo de 2005."),
        ("agente", "Gracias. Le llamo porque su tarjeta tiene un saldo pendiente de $480.000 con 35 días de mora. ¿Qué pasó con el pago?"),
        ("cliente", "Me quedé sin trabajo el mes pasado, la verdad no he podido."),
        ("agente", "Lamento mucho la situación. Le puedo ofrecer un acuerdo de pago en cuatro cuotas de $120.000 sin intereses de mora. ¿Le sirve?"),
        ("cliente", "Sí, así sí puedo."),
        ("agente", "Listo, el acuerdo quedó registrado. Le confirmo: cuatro cuotas de $120.000, la primera el 15. Le llega el soporte al correo. ¿Alguna otra inquietud?"),
        ("cliente", "No, muchas gracias."),
        ("agente", "Gracias a usted, que tenga un buen día."),
    ]


def cobranza_coercitiva(r, v):
    return "cobranza", "voz", "financiero", "saliente", [
        ("agente", f"Señor, le llamo de {EMPRESA['financiero']} por su deuda de $1.200.000."),
        ("cliente", "Ya hablé con ustedes ayer y les dije que pago el viernes."),
        ("agente", "Si no paga hoy vamos a llamar a su familia y a su jefe para que se enteren."),
        ("cliente", "Eso no es justo, no me pueden amenazar así."),
        ("agente", "Usted tenía que pagar a tiempo. Si no paga hay embargo inmediato."),
        ("cliente", "Voy a poner la queja en la Superfinanciera."),
    ]


def cliente_hostil_desescalada(r, v):
    return "soporte", "voz", "telecom", "entrante", [
        ("sistema", "Esta llamada será grabada para fines de calidad."),
        ("agente", f"Buenas noches, le habla {v['ag']} de {EMPRESA['telecom']}. ¿En qué le puedo ayudar?"),
        ("cliente", "¡¡Llevo cinco días sin servicio, son unos ineptos!! Es la cuarta vez que llamo y nadie me soluciona."),
        ("agente", "Tiene toda la razón en estar molesto, cinco días sin servicio es demasiado. Yo me encargo de su caso ahora mismo. ¿Me confirma su número de cédula?"),
        ("cliente", f"{v['ced']}. Y apúrele que ya estoy harto."),
        ("agente", "Gracias. Veo que hay una visita técnica que nunca se programó. Voy a escalarlo como prioritario y agendar la visita para mañana a las 8:00 a. m."),
        ("cliente", "¿Y si no vienen otra vez?"),
        ("agente", f"Le dejo el número de radicado {v['rad']} y mi compromiso: si la visita no se cumple, le aplicamos el descuento por los días sin servicio. Le confirmo: visita mañana a las 8:00 a. m."),
        ("cliente", "Bueno, gracias. Disculpe la grosería, es que estoy desesperado."),
        ("agente", "No se preocupe, lo entiendo. ¿Hay algo más en lo que le pueda ayudar?"),
        ("cliente", "No, gracias."),
        ("agente", "Que tenga una buena noche."),
    ]


def pide_otp(r, v):
    return "servicio", "voz", "financiero", "entrante", [
        ("agente", f"Buenas tardes, le habla {v['ag']} de {EMPRESA['financiero']}. ¿En qué le ayudo?"),
        ("cliente", "No puedo entrar a la app, me dice que el usuario está bloqueado."),
        ("agente", "Le voy a enviar un código a su celular. Me dicta el código que le llegó, por favor."),
        ("cliente", "Me llegó un mensaje que dice que no lo comparta con nadie..."),
        ("agente", "Tranquila, es para desbloquear. Me regala la clave de la app también."),
        ("cliente", "Mmm bueno, es 4821."),
        ("agente", "Listo, ya quedó desbloqueado."),
    ]


def soporte_transferencias(r, v):
    return "soporte", "voz", "general", "entrante", [
        ("agente", f"Buenas, le habla {v['ag']}, ¿en qué le ayudo?"),
        ("cliente", "La lavadora que compré no prende y está en garantía."),
        ("agente", "Me regala un momento."),
        ("agente", "Le voy a transferir al área de garantías."),
        ("agente", "Garantías, buenas. Me regala su número de cédula."),
        ("cliente", v["ced"]),
        ("agente", "Permítame un momento, ya regreso."),
        ("agente", "Eso no lo vemos aquí, le paso con el área de servicio técnico."),
        ("agente", "Servicio técnico. ¿Me confirma su cédula?"),
        ("cliente", "Otra vez? Ya la di dos veces. " + v["ced"]),
        ("agente", "Le voy a transferir a mi supervisor."),
        ("agente", "Le dejo el caso " + v["rad"] + ", lo llamamos."),
        ("cliente", "¿Y cuándo? Llevo una hora en esto."),
    ]


def seguimiento_reclamo(r, v):
    """Recontacto: el mismo cliente vuelve porque no le resolvieron."""
    return "servicio", "voz", "general", "entrante", [
        ("agente", f"Buenas tardes, le habla {v['ag']}. ¿En qué le puedo ayudar?"),
        ("cliente", "Llamo otra vez por lo mismo, ya les dije hace unos días y sigue igual. Es la tercera vez."),
        ("agente", "Lamento mucho que tenga que llamar de nuevo. Voy a revisar su caso ya mismo. ¿Me confirma su cédula?"),
        ("cliente", v["ced"]),
        ("agente", f"Gracias. Lo escalé como prioritario con el radicado {v['rad']}; tendrá respuesta en máximo 3 días hábiles. Le confirmo el número para su seguimiento."),
        ("cliente", "Bueno, espero que esta vez sí."),
        ("agente", "Que tenga buena tarde."),
    ]


ESCENARIOS: dict[str, Callable] = {
    "servicio_ejemplar": servicio_ejemplar,
    "bot_bucle_sin_humano": bot_bucle_sin_humano,
    "bot_a_persona_sin_contexto": bot_a_persona_sin_contexto,
    "bot_a_persona_con_contexto": bot_a_persona_con_contexto,
    "bot_resuelve": bot_resuelve,
    "bot_pide_humano_atendido": bot_pide_humano_atendido,
    "queja_radicada": queja_radicada,
    "agente_evasivo": agente_evasivo,
    "cancelacion_con_retencion": cancelacion_con_retencion,
    "cancelacion_correcta": cancelacion_correcta,
    "venta_correcta": venta_correcta,
    "venta_agresiva": venta_agresiva,
    "cobranza_respetuosa": cobranza_respetuosa,
    "cobranza_coercitiva": cobranza_coercitiva,
    "cliente_hostil_desescalada": cliente_hostil_desescalada,
    "pide_otp": pide_otp,
    "soporte_transferencias": soporte_transferencias,
}

# Mezcla de escenarios por periodo (pesos relativos).
MEZCLA = {
    "antes": {
        "servicio_ejemplar": 6, "bot_bucle_sin_humano": 10, "bot_a_persona_sin_contexto": 10, "bot_a_persona_con_contexto": 2,
        "bot_resuelve": 8, "bot_pide_humano_atendido": 2, "queja_radicada": 5, "agente_evasivo": 8, "cancelacion_con_retencion": 6, "cancelacion_correcta": 1,
        "venta_correcta": 3, "venta_agresiva": 6, "cobranza_respetuosa": 3, "cobranza_coercitiva": 4,
        "cliente_hostil_desescalada": 4, "pide_otp": 2, "soporte_transferencias": 6,
    },
    "despues": {
        "servicio_ejemplar": 12, "bot_bucle_sin_humano": 2, "bot_a_persona_sin_contexto": 3, "bot_a_persona_con_contexto": 10,
        "bot_resuelve": 12, "bot_pide_humano_atendido": 9, "queja_radicada": 8, "agente_evasivo": 2, "cancelacion_con_retencion": 1, "cancelacion_correcta": 6,
        "venta_correcta": 7, "venta_agresiva": 1, "cobranza_respetuosa": 6, "cobranza_coercitiva": 1,
        "cliente_hostil_desescalada": 5, "pide_otp": 0, "soporte_transferencias": 2,
    },
}
NO_RESUELTOS = {"bot_bucle_sin_humano", "agente_evasivo", "soporte_transferencias", "cancelacion_con_retencion"}
FUERA_DE_HORARIO = {"venta_agresiva", "cobranza_coercitiva"}


def _fecha(r: random.Random, base: datetime, escenario: str) -> datetime:
    dia = base + timedelta(days=r.randint(0, 27))
    if escenario in FUERA_DE_HORARIO:
        opcion = r.choice(["domingo", "noche", "sabado_tarde"])
        if opcion == "domingo":
            dia += timedelta(days=(6 - dia.weekday()) % 7)
            return dia.replace(hour=r.randint(9, 17), minute=r.randint(0, 59))
        if opcion == "sabado_tarde":
            dia += timedelta(days=(5 - dia.weekday()) % 7)
            return dia.replace(hour=r.randint(16, 18), minute=r.randint(0, 59))
        while dia.weekday() >= 5 or es_festivo(dia.date()):
            dia += timedelta(days=1)
        return dia.replace(hour=r.randint(19, 20), minute=r.randint(5, 59))
    while dia.weekday() == 6 or es_festivo(dia.date()):
        dia += timedelta(days=1)
    hora = r.randint(8, 14) if dia.weekday() == 5 else r.randint(7, 18)
    return dia.replace(hour=hora, minute=r.randint(0, 59))


def generar(n: int = 200, periodo: str = "antes", semilla: int = 11, inicio: datetime | None = None,
            prob_recontacto: float = 0.6) -> list[Conversacion]:
    r = random.Random(f"{semilla}-{periodo}")
    base = (inicio or datetime(2026, 9, 1 if periodo == "antes" else 29, 0, 0)).replace(tzinfo=HORA_COLOMBIA)
    mezcla = MEZCLA[periodo]
    nombres, pesos = zip(*[(k, w) for k, w in mezcla.items() if w > 0])
    convs: list[Conversacion] = []
    i = 0
    while len(convs) < n:
        esc = r.choices(nombres, weights=pesos)[0]
        v = {"ag": r.choice(AGENTES), "cli": r.choice(CLIENTES), "ced": _ced(r), "cel": _cel(r), "rad": _rad(r)}
        tipo, canal, sector, direccion, turnos = ESCENARIOS[esc](r, v)
        cliente = f"cli-{r.randint(1, 10**6):06d}"
        fecha = _fecha(r, base, esc)
        agente = f"A{AGENTES.index(v['ag']) + 1:02d}" if any(t[0] == "agente" for t in turnos) else None
        i += 1
        convs.append(_conv(f"{periodo[:3]}-{i:04d}", tipo, canal, sector, direccion, fecha, cliente, agente, turnos, esc))
        if esc in NO_RESUELTOS and direccion == "entrante" and r.random() < prob_recontacto and len(convs) < n:
            v2 = {**v, "ag": r.choice(AGENTES), "rad": _rad(r)}
            t2, c2, s2, d2, turnos2 = seguimiento_reclamo(r, v2)
            i += 1
            f2 = fecha + timedelta(days=r.randint(1, 5), hours=r.randint(0, 3))
            while f2.weekday() == 6 or es_festivo(f2.date()):
                f2 += timedelta(days=1)
            convs.append(_conv(f"{periodo[:3]}-{i:04d}", t2, c2, s2, d2, f2, cliente,
                               f"A{AGENTES.index(v2['ag']) + 1:02d}", turnos2, "seguimiento_reclamo"))
    if periodo == "antes":  # insistencia de cobranza: mismo cliente, mismo día, dos canales
        r2 = random.Random(semilla)
        cob = [c for c in convs if c.tipo == "cobranza"][:2]
        for c in cob:
            i += 1
            convs.append(_conv(f"ant-{i:04d}", "cobranza", "whatsapp", "financiero", "saliente",
                               c.inicio + timedelta(hours=2), c.cliente_id, c.agente_id,
                               [("agente", f"Buenas, le escribimos de {EMPRESA['financiero']}. Recuerde pagar su obligación hoy."),
                                ("cliente", "Ya me llamaron hoy, ¡dejen de fregar!")], "cobranza_insistente"))
        r2.shuffle(convs)
    return convs


def _conv(id_, tipo, canal, sector, direccion, fecha, cliente, agente, turnos, escenario) -> Conversacion:
    t_seg = 0.0
    lista = []
    for rol, texto in turnos:
        lista.append(Turno(rol=rol, texto=texto, t=round(t_seg, 1)))
        t_seg += 4 + len(texto) / (14 if canal == "voz" else 6)
    return Conversacion(id=id_, turnos=lista, tipo=tipo, canal=canal, sector=sector, direccion=direccion,
                        inicio=fecha, cliente_id=cliente, agente_id=agente, metadatos={"escenario": escenario})
