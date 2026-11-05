"""Rúbrica de Alómetro: criterios objetivos, auditables y con fundamento.

Reglas de diseño (inspiradas en la práctica COPC/ISO 18295 de monitoreo):

* Cada criterio dice **cuándo aplica**, **qué cuenta como cumplimiento** y
  **qué evidencia** lo respalda (turno + cita). Nada de «actitud» subjetiva.
* Los **errores críticos** se miden aparte, en tres categorías:
  - ``cliente``: el cliente queda peor o sin salida (p. ej. el bot niega un humano).
  - ``negocio``: riesgo comercial o de fraude (p. ej. venta sin aceptación expresa).
  - ``cumplimiento``: incumplimiento normativo colombiano (Ley 2300, Ley 1480, Res. CRC).
  Un error crítico anula la nota de la interacción (política por defecto, configurable)
  y se reporta como % de interacciones *libres* de error crítico.
* Los criterios que no aplican no suman ni restan: la nota es
  ``100 × puntos obtenidos / puntos aplicables``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .detectores import Senales
from .modelos import Conversacion, Evidencia

Resultado = tuple[bool, bool | None, str, list[Evidencia]]  # aplica, cumple, detalle, evidencias

DIMENSIONES = {
    "resolucion": "Resolución",
    "esfuerzo": "Esfuerzo del cliente",
    "trato": "Trato humano",
    "bot": "Asistente virtual",
    "proceso": "Proceso y guion",
    "cumplimiento": "Cumplimiento (Colombia)",
}


@dataclass(frozen=True)
class Criterio:
    id: str
    nombre: str
    dimension: str
    peso: int
    critico: str | None
    evaluar: Callable[[Conversacion, Senales], Resultado]
    recomendacion: str
    fundamento: str


NO_APLICA: Resultado = (False, None, "No aplica a esta interacción.", [])


def _ok(detalle: str, ev: list[Evidencia] | None = None) -> Resultado:
    return True, True, detalle, ev or []


def _falla(detalle: str, ev: list[Evidencia] | None = None) -> Resultado:
    return True, False, detalle, ev or []


def _ev(*xs: Evidencia | None) -> list[Evidencia]:
    return [x for x in xs if x is not None]


ATENCION = ("servicio", "soporte", "retencion", "cancelacion", "cobranza")


# ----------------------------- Resolución -----------------------------------
def r1_resolucion(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo == "ventas":
        return NO_APLICA
    if s.resolucion == "resuelto":
        return _ok("La solicitud quedó resuelta en el contacto.", s.evidencia_resolucion)
    if s.resolucion == "en_tramite" and s.plazo:
        return _ok("No se resolvió en el contacto, pero quedó radicada con número y plazo.", _ev(s.radicado, s.plazo))
    if s.resolucion == "en_tramite":
        return _falla("Quedó radicada pero sin plazo de respuesta informado.", _ev(s.radicado))
    if s.resolucion == "no_resuelto":
        return _falla("La solicitud no se resolvió.", s.evidencia_resolucion)
    return _falla("No hay evidencia de resolución ni de trámite formal.", [])


def r2_radicado(c: Conversacion, s: Senales) -> Resultado:
    if not s.queja and c.tipo != "cancelacion":
        return NO_APLICA
    if s.resolucion == "resuelto" and c.tipo != "cancelacion":
        return _ok("La queja se resolvió en el mismo contacto.", s.evidencia_resolucion)
    if c.tipo == "cancelacion":
        if s.radicado:
            return _ok("La cancelación quedó radicada con número.", [s.radicado])
        return _falla("La cancelación no quedó radicada con número (CUN en telecomunicaciones).")
    if s.radicado and s.plazo:
        return _ok("Se entregó número de radicado y plazo de respuesta.", _ev(s.radicado, s.plazo))
    if s.radicado:
        return _falla("Se dio radicado pero no el plazo de respuesta.", _ev(s.queja, s.radicado))
    return _falla("Hubo queja o solicitud formal y no se entregó número de radicado.", _ev(s.queja))


def r3_sin_salida(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo == "ventas":
        return NO_APLICA
    if s.resolucion != "no_resuelto":
        return _ok("El cliente no quedó sin salida.")
    if s.radicado or s.transferencias:
        return _ok("No se resolvió, pero se dejó un siguiente paso concreto (radicado o traslado).", _ev(s.radicado, *s.transferencias[:1]))
    return _falla("El cliente terminó sin solución y sin siguiente paso (callejón sin salida).", s.evidencia_resolucion)


# ------------------------------ Esfuerzo ------------------------------------
def e1_transferencias(c: Conversacion, s: Senales) -> Resultado:
    # El paso bot -> persona se evalúa en la dimensión del bot; aquí cuentan los traslados entre personas/áreas.
    tr = [e for e in s.transferencias if e.rol != "bot"]
    if len(tr) <= 1:
        return _ok(f"{len(tr)} transferencia(s) entre áreas.", tr)
    return _falla(f"{len(tr)} transferencias: el cliente tuvo que contar su caso varias veces.", tr)


def e2_contexto(c: Conversacion, s: Senales) -> Resultado:
    if not s.datos_repedidos:
        return _ok("No se pidieron de nuevo datos que el cliente ya había dado.")
    return _falla("Se pidieron de nuevo datos que el cliente ya había entregado (pérdida de contexto).", s.datos_repedidos)


def e3_redireccion(c: Conversacion, s: Senales) -> Resultado:
    if not s.redirecciones:
        return _ok("No se envió al cliente a otro canal.")
    if s.resolucion in ("resuelto", "en_tramite"):
        return _ok("Se mencionó otro canal, pero la solicitud quedó resuelta o radicada.", s.redirecciones[:1])
    return _falla("Se envió al cliente a otro canal sin resolver su solicitud.", s.redirecciones)


def e4_esperas(c: Conversacion, s: Senales) -> Resultado:
    n = len(s.esperas)
    if n <= 2:
        return _ok(f"{n} espera(s).", s.esperas)
    return _falla(f"{n} esperas en un mismo contacto.", s.esperas)


def e5_repeticion(c: Conversacion, s: Senales) -> Resultado:
    if not s.repeticiones_cliente:
        return _ok("El cliente no tuvo que repetir su mensaje.")
    return _falla("El cliente tuvo que repetir el mismo mensaje (no fue entendido).", s.repeticiones_cliente)


# ------------------------------- Trato --------------------------------------
def t1_validacion(c: Conversacion, s: Senales) -> Resultado:
    if s.frustracion_max < 3:
        return NO_APLICA
    if s.validacion:
        return _ok("Reconoció la emoción o la molestia del cliente.", s.validacion[:2])
    return _falla("El cliente mostró frustración y nadie la reconoció.", _ev(s.pico_frustracion))


def t2_escucha(c: Conversacion, s: Senales) -> Resultado:
    if (c.tipo == "cobranza" and not s.queja) or (not c.hubo_agente and not s.queja):
        return NO_APLICA
    if s.parafraseo or (s.guion.get("resumen") is not None):
        return _ok("Confirmó haber entendido (parafraseo o resumen).", _ev(*(s.parafraseo[:1]), s.guion.get("resumen")))
    return _falla("No parafraseó ni confirmó lo que entendió de la solicitud.")


def t3_apropiacion(c: Conversacion, s: Senales) -> Resultado:
    if not c.hubo_agente:
        return NO_APLICA
    if s.apropiacion:
        return _ok("Usó lenguaje de responsabilidad («yo me encargo», «voy a…»).", s.apropiacion[:1])
    hecho = [e for e in s.evidencia_resolucion if e.rol == "agente"]
    if hecho:
        return _ok("Se hizo cargo y ejecutó la solución.", hecho[:1])
    return _falla("No hubo lenguaje de apropiación del caso.")


def t4_culpa(c: Conversacion, s: Senales) -> Resultado:
    malos = s.culpa_evasion + s.negativo_sin_alternativa
    if not malos:
        return _ok("Sin frases que culpen al cliente ni negativas sin alternativa.")
    return _falla("Usó frases que culpan, evaden o niegan sin ofrecer alternativa.", malos)


def t5_respeto(c: Conversacion, s: Senales) -> Resultado:
    if s.irrespeto_agente:
        return _falla("Trato irrespetuoso hacia el cliente.", s.irrespeto_agente)
    return _ok("Trato respetuoso.")


def t6_desescala(c: Conversacion, s: Senales) -> Resultado:
    if s.frustracion_inicial < 3 or len(s.frustracion) < 2:
        return NO_APLICA
    if s.trayectoria == "desescalada":
        return _ok(f"La frustración bajó de {s.frustracion_inicial:.0f} a {s.frustracion_final:.1f} (de 10).")
    return _falla(f"El cliente empezó frustrado ({s.frustracion_inicial:.0f}/10) y terminó igual o peor ({s.frustracion_final:.1f}/10).", _ev(s.pico_frustracion))


def t7_empatia_guion(c: Conversacion, s: Senales) -> Resultado:
    if s.disculpas_guion >= 3:
        return _falla(f"Repitió {s.disculpas_guion} veces una disculpa de plantilla: suena a guion, no a empatía.")
    return _ok("Sin disculpas de plantilla repetidas.")


# ------------------------------ Asistente virtual ---------------------------
def b1_transparencia(c: Conversacion, s: Senales) -> Resultado:
    if not c.hubo_bot:
        return NO_APLICA
    if s.bot_se_identifica:
        return _ok("El asistente se presentó como asistente virtual.")
    return _falla("El asistente no dijo que es un asistente virtual en sus primeros mensajes.")


def b2_salida_humano(c: Conversacion, s: Senales) -> Resultado:
    if not c.hubo_bot or not s.peticiones_humano:
        return NO_APLICA
    if s.humano_atendido and (s.pasos_bot_hasta_humano or 0) <= 2:
        return _ok(f"Pidió una persona y la obtuvo tras {s.pasos_bot_hasta_humano} respuesta(s) del bot.", s.peticiones_humano[:1])
    if s.humano_atendido:
        return _falla(f"Pidió una persona y el bot tardó {s.pasos_bot_hasta_humano} respuestas en pasarlo.", s.peticiones_humano)
    if len(s.peticiones_humano) >= 2:
        return _falla(f"Pidió una persona {len(s.peticiones_humano)} veces y nunca se la dieron.", s.peticiones_humano)
    return _falla("Pidió una persona y no se la dieron.", s.peticiones_humano)


def b2c_humano_negado(c: Conversacion, s: Senales) -> Resultado:
    if not c.hubo_bot or not s.peticiones_humano:
        return NO_APLICA
    if s.humano_atendido is False and len(s.peticiones_humano) >= 2:
        return _falla("Atención humana negada: pidió una persona varias veces y el bot no lo transfirió.", s.peticiones_humano)
    return _ok("No se negó la atención humana.")


def b3_bucles(c: Conversacion, s: Senales) -> Resultado:
    if not c.hubo_bot:
        return NO_APLICA
    if s.bucles_bot or len(s.fallbacks_bot) >= 2:
        return _falla("El bot entró en bucle (repitió respuestas o «no entendí» varias veces).", s.bucles_bot + s.fallbacks_bot)
    return _ok("Sin bucles del bot.")


def b4_traspaso(c: Conversacion, s: Senales) -> Resultado:
    if not (c.hubo_bot and c.hubo_agente):
        return NO_APLICA
    if s.datos_repedidos:
        return _falla("En el traspaso del bot a la persona se perdió el contexto.", s.datos_repedidos)
    if s.contexto_reconocido:
        return _ok("La persona retomó lo que el cliente ya había dicho al bot.", [s.contexto_reconocido])
    return _ok("No se pidieron datos repetidos en el traspaso (no hubo mención explícita del contexto).")


def b5_contencion(c: Conversacion, s: Senales) -> Resultado:
    if not c.hubo_bot or c.hubo_agente:
        return NO_APLICA
    if s.resolucion in ("resuelto", "en_tramite") and not s.abandono:
        return _ok("El bot resolvió sin necesidad de una persona (contención real).", s.evidencia_resolucion)
    if s.resolucion == "incierto" and not s.abandono and s.frustracion_final < 3:
        return _ok("Conversación solo con el bot, sin señales de fracaso.")
    return _falla("El cliente se fue del bot sin solución: es una «contención» falsa.", s.evidencia_resolucion + s.peticiones_humano[-1:])


# ------------------------------ Proceso -------------------------------------
def _paso(clave: str, ok: str, falla: str, aplica: Callable[[Conversacion], bool] = lambda c: True):
    def f(c: Conversacion, s: Senales) -> Resultado:
        if not aplica(c):
            return NO_APLICA
        e = s.guion.get(clave)
        return _ok(ok, [e]) if e else _falla(falla)
    return f


p1_saludo = _paso("saludo", "Saludó al iniciar.", "No hubo saludo al iniciar.")
p2_identificacion = _paso("identificacion", "Se identificó (nombre o asistente virtual).", "No se identificó quién atiende.")
def p3_indagacion(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo == "cobranza":
        return NO_APLICA
    e = s.guion.get("indagacion")
    if e:
        return _ok("Indagó la necesidad del cliente.", [e])
    if s.parafraseo or s.contexto_reconocido:
        return _ok("Confirmó la necesidad que el cliente ya había expresado.", _ev(*(s.parafraseo[:1]), s.contexto_reconocido))
    return _falla("No preguntó ni exploró la necesidad.")
p5_resumen = _paso("resumen", "Resumió o confirmó lo acordado.", "No resumió lo acordado antes de cerrar.")
p6_ayuda = _paso("ayuda_adicional", "Ofreció ayuda adicional.", "No ofreció ayuda adicional antes de cerrar.")
p7_despedida = _paso("despedida", "Cerró con una despedida cordial.", "No hubo despedida.")


def p4_verificacion(c: Conversacion, s: Senales) -> Resultado:
    if s.verificacion_antes_de_info is None:
        return NO_APLICA
    if s.verificacion_antes_de_info:
        return _ok("Verificó la identidad antes de dar información de la cuenta.", _ev(s.info_cuenta))
    return _falla("Dio información de la cuenta sin verificar antes la identidad.", _ev(s.info_cuenta))


def p8_grabacion(c: Conversacion, s: Senales) -> Resultado:
    if c.canal != "voz":
        return NO_APLICA
    e = s.guion.get("aviso_grabacion")
    return _ok("Avisó que la llamada se graba.", [e]) if e else _falla("No avisó que la llamada se graba o monitorea.")


# ---------------------------- Cumplimiento ----------------------------------
def l1_horario(c: Conversacion, s: Senales) -> Resultado:
    if s.ventana_legal is None:
        return NO_APLICA
    ok, motivo = s.ventana_legal
    return _ok(f"Contacto en horario permitido ({motivo}).") if ok else _falla(f"Contacto fuera del horario permitido por la Ley 2300 de 2023: {motivo}.")


def l2_retracto(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo != "ventas" or not s.venta_cerrada:
        return NO_APLICA
    if s.retracto:
        return _ok("Informó el derecho de retracto.", [s.retracto])
    return _falla("Cerró una venta a distancia sin informar el derecho de retracto (5 días hábiles).", [s.venta_cerrada])


def l3_aceptacion(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo != "ventas" or not s.venta_cerrada:
        return NO_APLICA
    if s.aceptacion:
        return _ok("El cliente aceptó de forma expresa.", [s.aceptacion])
    return _falla("Se dio la venta por cerrada sin una aceptación expresa del cliente.", [s.venta_cerrada])


def l4_info_venta(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo != "ventas" or not s.venta_cerrada:
        return NO_APLICA
    faltan = [n for n, e in (("precio", s.precio), ("condiciones/permanencia", s.condiciones)) if e is None]
    if not faltan:
        return _ok("Informó precio y condiciones.", _ev(s.precio, s.condiciones))
    return _falla("Faltó informar: " + ", ".join(faltan) + ".", [s.venta_cerrada])


def l5_autorizacion(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo != "ventas" or not s.datos_personales_pedidos:
        return NO_APLICA
    if s.autorizacion_datos:
        return _ok("Pidió autorización para el tratamiento de datos.", [s.autorizacion_datos])
    return _falla("Recolectó datos personales sin pedir autorización de tratamiento (Ley 1581 de 2012).")


def l6_rechazo(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo != "ventas" or len(s.rechazos_cliente) < 2:
        return NO_APLICA
    if s.insistencia_tras_rechazo:
        return _falla("Siguió ofreciendo después de que el cliente dijo que no dos veces.", s.rechazos_cliente[:2] + s.insistencia_tras_rechazo[:1])
    return _ok("Respetó la negativa del cliente.")


def l7_cancelacion(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo != "cancelacion":
        return NO_APLICA
    if s.retencion_antes_de_radicar:
        return _falla("Ofreció retención antes de radicar la cancelación: el cliente pidió cancelar, no una oferta.", [s.retencion_antes_de_radicar])
    if c.sector == "telecom" and s.ofertas_en_cancelacion:
        return _falla("En telecomunicaciones no se pueden hacer ofertas de retención en el canal de cancelación (Res. CRC 8171 de 2026).", s.ofertas_en_cancelacion)
    if not s.radicado:
        return _falla("No se entregó número de radicado (CUN en telecomunicaciones) de la cancelación.")
    return _ok("Radicó la cancelación sin obstáculos de retención.", [s.radicado])


def l8_coercion(c: Conversacion, s: Senales) -> Resultado:
    if c.tipo != "cobranza":
        return NO_APLICA
    if s.coercion:
        return _falla("Amenazas o presión indebida (terceros, visitas, cárcel, embargo inmediato).", s.coercion)
    return _ok("Cobranza sin amenazas ni presión indebida.")


def l9_credenciales(c: Conversacion, s: Senales) -> Resultado:
    if s.pide_credencial or s.datos_expuestos:
        return _falla("Pidió o expuso datos que nunca se deben pedir (clave, PIN, CVV, código OTP o tarjeta completa).", s.pide_credencial + s.datos_expuestos)
    return _ok("No pidió claves, PIN ni códigos de seguridad.")


CRITERIOS: list[Criterio] = [
    Criterio("R1", "Resuelve o deja trámite formal", "resolucion", 20, None, r1_resolucion,
             "Cierre cada contacto con una solución confirmada o con un radicado y un plazo concretos.",
             "Resolución en el primer contacto (FCR): evita el recontacto, que es costo para la empresa y esfuerzo para el cliente."),
    Criterio("R2", "Radicado y plazo ante queja", "resolucion", 10, None, r2_radicado,
             "Ante toda queja o reclamo entregue el número de radicado (CUN en telecomunicaciones) y el plazo legal de respuesta.",
             "En telecomunicaciones la PQR se identifica con CUN y el operador tiene 15 días hábiles; en general la queja debe quedar trazable."),
    Criterio("R3", "Sin callejón sin salida", "resolucion", 0, "cliente", r3_sin_salida,
             "Si no puede resolver, nunca termine sin un siguiente paso: radique, escale o agende.",
             "Un cliente sin solución ni camino convierte su caso en PQR, en queja ante la SIC o la CRC, o en abandono."),
    Criterio("E1", "Máximo una transferencia", "esfuerzo", 8, None, e1_transferencias,
             "Resuelva o transfiera una sola vez, con el caso documentado.",
             "Cada transferencia obliga a repetir el caso y aumenta el esfuerzo del cliente (CES)."),
    Criterio("E2", "No pide datos ya entregados", "esfuerzo", 10, None, e2_contexto,
             "Lea el historial y lo que el cliente ya dio antes de pedirle datos.",
             "Escalar a una persona sin perder el contexto es la función más valorada de un chatbot bancario en Colombia (63 %, Delto 2025)."),
    Criterio("E3", "No manda a otro canal sin resolver", "esfuerzo", 6, None, e3_redireccion,
             "Si otro canal es necesario, deje radicado el caso antes de enviarlo allí.",
             "Desviar al cliente («escriba al correo», «vaya a una oficina») traslada el esfuerzo al cliente."),
    Criterio("E4", "Esperas razonables", "esfuerzo", 4, None, e4_esperas,
             "Agrupe las consultas internas para no poner al cliente en espera varias veces.",
             "Varias esperas seguidas indican que quien atiende no tiene la información a mano y alargan el contacto."),
    Criterio("E5", "El cliente no repite su mensaje", "esfuerzo", 5, None, e5_repeticion,
             "Si el cliente repite algo, es señal de que no se le entendió: confirme y cambie de enfoque.",
             "La repetición es un indicador directo de comprensión fallida."),
    Criterio("T1", "Reconoce la emoción del cliente", "trato", 10, None, t1_validacion,
             "Nombre la emoción antes de la solución: «Entiendo su molestia, llevar tres días sin servicio es mucho».",
             "Validación emocional: reduce la activación y abre la escucha (base de la desescalada)."),
    Criterio("T2", "Escucha activa", "trato", 6, None, t2_escucha,
             "Parafrasee la solicitud: «Si le entiendo bien, el cobro de octubre no corresponde…».",
             "Parafrasear confirma comprensión y evita resolver el problema equivocado."),
    Criterio("T3", "Se hace cargo del caso", "trato", 5, None, t3_apropiacion,
             "Use lenguaje de responsabilidad: «Yo me encargo», «Voy a revisar…».",
             "El lenguaje de apropiación aumenta la confianza en la solución."),
    Criterio("T4", "Sin culpar ni negar sin alternativa", "trato", 8, None, t4_culpa,
             "Cambie «no se puede» por «lo que sí puedo hacer es…» y nunca culpe al cliente.",
             "Las negativas secas y la culpa al cliente disparan la frustración."),
    Criterio("T5", "Trato respetuoso", "trato", 0, "cliente", t5_respeto,
             "Tolerancia cero al irrespeto. Si el cliente agrede, aplique el protocolo de llamada difícil.",
             "El irrespeto al cliente es un error crítico en cualquier modelo de calidad."),
    Criterio("T6", "Baja la frustración", "trato", 8, None, t6_desescala,
             "Valide, explique qué va a hacer y en cuánto tiempo, y confirme al final.",
             "El estado emocional con el que termina la conversación es lo que el cliente recuerda de la marca."),
    Criterio("T7", "Empatía real, no de plantilla", "trato", 3, None, t7_empatia_guion,
             "Evite repetir «lamentamos los inconvenientes»: personalice la disculpa una sola vez.",
             "La disculpa repetida de guion se percibe como indiferencia."),
    Criterio("B1", "El asistente dice que es virtual", "bot", 5, None, b1_transparencia,
             "Configure el primer mensaje: «Soy el asistente virtual de…; si lo prefiere, le paso con una persona».",
             "Transparencia: los proyectos de ley de IA en Colombia piden avisar cuando se habla con una IA."),
    Criterio("B2", "Pasa a una persona cuando se pide", "bot", 12, None, b2_salida_humano,
             "Transfiera a una persona como máximo en la segunda respuesta después de que la pidan.",
             "El 60 % de los clientes teme que la IA le impida llegar a una persona (Gartner, encuesta a 5.728 clientes, 2024)."),
    Criterio("B2C", "No niega la atención humana", "bot", 0, "cliente", b2c_humano_negado,
             "Nunca bloquee la salida a humano: la petición repetida debe forzar el traspaso.",
             "La preferencia por la atención humana es el motivo más citado para abandonar los chatbots bancarios en Colombia (39 %, Delto 2025)."),
    Criterio("B3", "Sin bucles del bot", "bot", 10, None, b3_bucles,
             "Tras dos «no entendí» seguidos, ofrezca una persona automáticamente.",
             "El «bucle sin salida» (doom loop) infla la contención y destruye la satisfacción."),
    Criterio("B4", "Traspaso con contexto", "bot", 8, None, b4_traspaso,
             "Pase a la persona la intención, los datos verificados y lo ya intentado.",
             "Escalar a un humano sin perder el contexto es la función más valorada de un chatbot bancario (63 %, Delto 2025)."),
    Criterio("B5", "Contención real, no falsa", "bot", 0, "cliente", b5_contencion,
             "Mida la contención solo cuando el cliente resolvió; si no, debe salir a una persona.",
             "Un bot que «retiene» clientes sin resolverles es una contención falsa: el problema vuelve por otro canal."),
    Criterio("P1", "Saludo", "proceso", 2, None, p1_saludo, "Salude al iniciar.", "Protocolo básico de apertura."),
    Criterio("P2", "Identificación de quien atiende", "proceso", 3, None, p2_identificacion,
             "Diga su nombre y la empresa (o que es un asistente virtual).", "El cliente debe saber con quién habla."),
    Criterio("P3", "Indaga la necesidad", "proceso", 4, None, p3_indagacion,
             "Pregunte de forma abierta y deje que el cliente explique.", "Sin diagnóstico no hay solución correcta."),
    Criterio("P4", "Verifica identidad antes de dar datos", "proceso", 8, None, p4_verificacion,
             "Valide la identidad antes de dar saldos, deudas o datos de la cuenta.", "Protección de datos personales y prevención de fraude."),
    Criterio("P5", "Resume lo acordado", "proceso", 4, None, p5_resumen,
             "Antes de cerrar, resuma: qué se hizo, qué sigue y cuándo.", "El resumen reduce el recontacto por malentendidos."),
    Criterio("P6", "Ofrece ayuda adicional", "proceso", 2, None, p6_ayuda, "Pregunte si hay algo más.", "Cierre completo."),
    Criterio("P7", "Despedida cordial", "proceso", 2, None, p7_despedida, "Despídase con cordialidad.", "Protocolo de cierre."),
    Criterio("P8", "Aviso de grabación", "proceso", 3, None, p8_grabacion,
             "Informe al inicio que la llamada se graba y para qué.", "Transparencia en el tratamiento de datos (Ley 1581 de 2012)."),
    Criterio("L1", "Horario legal de contacto", "cumplimiento", 0, "cumplimiento", l1_horario,
             "Programe las campañas salientes solo de lunes a viernes de 7:00 a 19:00 y sábados de 8:00 a 15:00, sin domingos ni festivos.",
             "Ley 2300 de 2023 («Dejen de fregar»), art. 3."),
    Criterio("L2", "Informa el derecho de retracto", "cumplimiento", 0, "cumplimiento", l2_retracto,
             "En toda venta telefónica o digital informe los 5 días hábiles para retractarse.",
             "Ley 1480 de 2011 (Estatuto del Consumidor), art. 47; Decreto 1074 de 2015."),
    Criterio("L3", "Aceptación expresa de la venta", "cumplimiento", 0, "negocio", l3_aceptacion,
             "Pregunte «¿Acepta…?» y espere un «sí, acepto» claro antes de activar.",
             "Sin aceptación expresa la venta es reversible y genera reclamos por cobros no autorizados."),
    Criterio("L4", "Precio y condiciones claros", "cumplimiento", 8, None, l4_info_venta,
             "Diga el precio total, la permanencia y cuándo cambia el precio promocional.",
             "Información clara, veraz y suficiente (Ley 1480 de 2011)."),
    Criterio("L5", "Autorización de datos personales", "cumplimiento", 6, None, l5_autorizacion,
             "Pida autorización de tratamiento de datos antes de registrar datos personales.",
             "Ley 1581 de 2012 (Habeas Data)."),
    Criterio("L6", "Respeta el «no» del cliente", "cumplimiento", 8, None, l6_rechazo,
             "Tras dos negativas, agradezca y cierre.",
             "La insistencia tras una negativa es la práctica que la Ley 2300 de 2023 («Dejen de fregar») busca frenar."),
    Criterio("L7", "Cancelación sin trabas", "cumplimiento", 0, "cumplimiento", l7_cancelacion,
             "Radique primero la cancelación y entregue el número; cualquier oferta, después y por otro canal.",
             "Res. CRC 8171 de 2026 (servicios móviles): canal de cancelación sin ofertas de retención y con envío del CUN."),
    Criterio("L8", "Cobranza sin coerción", "cumplimiento", 0, "cumplimiento", l8_coercion,
             "Nunca amenace ni mencione a terceros, visitas o consecuencias penales.",
             "Ley 2300 de 2023: prohíbe visitas al domicilio o trabajo y contactar a terceros; prácticas abusivas de cobranza."),
    Criterio("L9", "Nunca pide claves ni códigos", "cumplimiento", 0, "negocio", l9_credenciales,
             "Nunca pida clave, PIN, CVV ni códigos OTP: diga «nunca se los pediremos».",
             "Es la puerta de entrada del fraude por suplantación (vishing)."),
]

CRITERIOS_POR_ID = {c.id: c for c in CRITERIOS}
