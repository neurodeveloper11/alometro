"""Detectores de señales: convierten una conversación en hechos verificables.

Cada señal guarda evidencias (turno + cita textual) para que cualquier persona
de calidad pueda auditar por qué Alómetro concluyó lo que concluyó. No hay
modelos opacos: son reglas explícitas y revisables (ver `lexicos.py`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import lexicos as L
from .calendario import ventana_ley_2300
from .modelos import Conversacion, Evidencia
from .texto import buscar, contar, jaccard, luhn_valido, normalizar, palabras, proporcion_mayusculas, recortar

EMPRESA = ("agente", "bot", "sistema")


@dataclass
class Senales:
    # Bot y salida a humano
    peticiones_humano: list[Evidencia] = field(default_factory=list)
    humano_atendido: bool | None = None
    pasos_bot_hasta_humano: int | None = None
    bot_se_identifica: bool | None = None
    bot_ofrece_humano: bool | None = None
    bucles_bot: list[Evidencia] = field(default_factory=list)
    fallbacks_bot: list[Evidencia] = field(default_factory=list)
    repeticiones_cliente: list[Evidencia] = field(default_factory=list)
    datos_repedidos: list[Evidencia] = field(default_factory=list)
    contexto_reconocido: Evidencia | None = None
    abandono: bool = False
    sin_respuesta: Evidencia | None = None
    # Emoción
    frustracion: list[float] = field(default_factory=list)
    frustracion_inicial: float = 0.0
    frustracion_final: float = 0.0
    frustracion_max: float = 0.0
    trayectoria: str = "sin_datos"
    pico_frustracion: Evidencia | None = None
    amenazas_externas: list[Evidencia] = field(default_factory=list)
    insultos_cliente: list[Evidencia] = field(default_factory=list)
    # Resolución
    resolucion: str = "incierto"
    evidencia_resolucion: list[Evidencia] = field(default_factory=list)
    queja: Evidencia | None = None
    radicado: Evidencia | None = None
    plazo: Evidencia | None = None
    # Esfuerzo
    transferencias: list[Evidencia] = field(default_factory=list)
    esperas: list[Evidencia] = field(default_factory=list)
    redirecciones: list[Evidencia] = field(default_factory=list)
    # Guion
    guion: dict[str, Evidencia | None] = field(default_factory=dict)
    verificacion_antes_de_info: bool | None = None
    info_cuenta: Evidencia | None = None
    # Trato
    validacion: list[Evidencia] = field(default_factory=list)
    parafraseo: list[Evidencia] = field(default_factory=list)
    apropiacion: list[Evidencia] = field(default_factory=list)
    culpa_evasion: list[Evidencia] = field(default_factory=list)
    negativo_sin_alternativa: list[Evidencia] = field(default_factory=list)
    disculpas_guion: int = 0
    irrespeto_agente: list[Evidencia] = field(default_factory=list)
    # Ventas
    venta_cerrada: Evidencia | None = None
    precio: Evidencia | None = None
    condiciones: Evidencia | None = None
    retracto: Evidencia | None = None
    autorizacion_datos: Evidencia | None = None
    aceptacion: Evidencia | None = None
    datos_personales_pedidos: bool = False
    rechazos_cliente: list[Evidencia] = field(default_factory=list)
    insistencia_tras_rechazo: list[Evidencia] = field(default_factory=list)
    # Cancelación, cobranza, seguridad, ley
    ofertas_en_cancelacion: list[Evidencia] = field(default_factory=list)
    retencion_antes_de_radicar: Evidencia | None = None
    coercion: list[Evidencia] = field(default_factory=list)
    pide_credencial: list[Evidencia] = field(default_factory=list)
    datos_expuestos: list[Evidencia] = field(default_factory=list)
    ventana_legal: tuple[bool, str] | None = None
    # Resumen
    temas: list[str] = field(default_factory=list)
    esfuerzo: int = 0
    carga_emocional: int | None = None

    def resumen(self) -> dict:
        """Versión compacta y serializable para informes y tableros."""
        return {
            "resolucion": self.resolucion,
            "trayectoria_emocional": self.trayectoria,
            "frustracion_inicial": round(self.frustracion_inicial, 1),
            "frustracion_final": round(self.frustracion_final, 1),
            "frustracion_max": round(self.frustracion_max, 1),
            "peticiones_humano": len(self.peticiones_humano),
            "humano_atendido": self.humano_atendido,
            "pasos_bot_hasta_humano": self.pasos_bot_hasta_humano,
            "bucle_bot": bool(self.bucles_bot) or len(self.fallbacks_bot) >= 2,
            "datos_repedidos": len(self.datos_repedidos),
            "transferencias": len(self.transferencias),
            "esperas": len(self.esperas),
            "redirecciones": len(self.redirecciones),
            "esfuerzo": self.esfuerzo,
            "carga_emocional_agente": self.carga_emocional,
            "amenaza_externa": bool(self.amenazas_externas),
            "abandono": self.abandono,
            "sin_respuesta": self.sin_respuesta is not None,
            "queja": self.queja is not None,
            "radicado": self.radicado is not None,
            "plazo": self.plazo is not None,
            "temas": self.temas,
            "ventana_legal": None if self.ventana_legal is None else {"permitido": self.ventana_legal[0], "motivo": self.ventana_legal[1]},
        }


def _ev(i: int, rol: str, texto: str, fragmento: str | None = None) -> Evidencia:
    """Evidencia con la cita centrada en el fragmento detectado (si se da)."""
    cita = texto
    if fragmento:
        norm = normalizar(texto)
        pos = norm.find(fragmento)
        if pos >= 0 and len(texto) > 160:
            ini = max(0, pos - 60)
            cita = ("…" if ini else "") + texto[ini:]
    return Evidencia(turno=i + 1, rol=rol, cita=recortar(cita))


_DIGITOS = re.compile(r"\d")
_DATO_DADO = {
    "documento": lambda n, raw: len(_DIGITOS.findall(raw)) >= 5 or "[numero]" in n or "[cedula]" in n,
    "telefono": lambda n, raw: len(_DIGITOS.findall(raw)) >= 7 or "[telefono]" in n,
    "cuenta": lambda n, raw: len(_DIGITOS.findall(raw)) >= 4 or "[numero]" in n,
    "correo": lambda n, raw: "@" in raw or "[correo]" in n,
    "nombre": lambda n, raw: len(palabras(n)) >= 2 or "[nombre]" in n,
    "direccion": lambda n, raw: bool(re.search(r"\b(calle|carrera|cra|cl|avenida|av|diagonal|transversal|kr|manzana|barrio)\b", n)) or "[direccion]" in n,
}


def _puntaje_frustracion(texto: str, norm: str) -> float:
    p = 3 * contar(L.FRUSTRACION_FUERTE, norm) + 2 * contar(L.FRUSTRACION_MEDIA, norm) + contar(L.FRUSTRACION_LEVE, norm)
    if buscar(L.AMENAZA_EXTERNA, norm):
        p += 3
    p += 3 * min(2, contar(L.INSULTOS, norm))
    if "!!" in texto or "¡¡" in texto:
        p += 1
    if "??" in texto or "¿¿" in texto:
        p += 1
    if proporcion_mayusculas(texto) > 0.6:
        p += 2
    p += min(4, 2 * contar(L.FRUSTRACION_EMOJI, texto))
    if buscar(L.POSITIVO_CLIENTE, norm):
        p -= 2
    return float(max(0, min(10, p)))


def analizar(conv: Conversacion) -> Senales:
    s = Senales()
    turnos = conv.turnos
    norms = [normalizar(t.texto) for t in turnos]
    idx_cliente = [i for i, t in enumerate(turnos) if t.rol == "cliente"]
    idx_empresa = [i for i, t in enumerate(turnos) if t.rol in EMPRESA]
    idx_agente = [i for i, t in enumerate(turnos) if t.rol == "agente"]
    idx_bot = [i for i, t in enumerate(turnos) if t.rol == "bot"]
    hubo_bot, hubo_agente = bool(idx_bot), bool(idx_agente)

    # ---------------- Emoción del cliente ----------------
    vistos: list[int] = []
    for i in idx_cliente:
        t, n = turnos[i], norms[i]
        f = _puntaje_frustracion(t.texto, n)
        # Repetir lo mismo es señal de no ser entendido.
        if len(palabras(n)) >= 3 and any(jaccard(n, norms[j]) >= 0.8 for j in vistos):
            s.repeticiones_cliente.append(_ev(i, "cliente", t.texto))
            f = min(10.0, f + 1)
        vistos.append(i)
        s.frustracion.append(f)
        frag = buscar(L.AMENAZA_EXTERNA, n)
        if frag:
            s.amenazas_externas.append(_ev(i, "cliente", t.texto, frag))
        frag = buscar(L.INSULTOS, n)
        if frag:
            s.insultos_cliente.append(_ev(i, "cliente", t.texto, frag))
        frag = buscar(L.QUEJA_CLIENTE, n)
        if frag and s.queja is None:
            s.queja = _ev(i, "cliente", t.texto, frag)
        frag = buscar(L.RECHAZO_CLIENTE, n)
        if frag:
            s.rechazos_cliente.append(_ev(i, "cliente", t.texto, frag))

    if s.frustracion:
        n_f = len(s.frustracion)
        k_ini = max(1, n_f // 3)
        k_fin = 2 if n_f >= 4 else 1
        s.frustracion_inicial = max(s.frustracion[:k_ini])
        s.frustracion_final = sum(s.frustracion[-k_fin:]) / k_fin
        s.frustracion_max = max(s.frustracion)
        pico = idx_cliente[s.frustracion.index(s.frustracion_max)]
        if s.frustracion_max > 0:
            s.pico_frustracion = _ev(pico, "cliente", turnos[pico].texto)
        if len(s.frustracion) < 2:
            s.trayectoria = "sin_datos" if s.frustracion_max < 3 else "sostenida"
        elif s.frustracion_inicial >= 3 and s.frustracion_final <= s.frustracion_inicial - 2:
            s.trayectoria = "desescalada"
        elif s.frustracion_final >= s.frustracion_inicial + 2 and s.frustracion_final >= 3:
            s.trayectoria = "escalada"
        elif s.frustracion_inicial >= 3 and s.frustracion_final >= 3:
            s.trayectoria = "sostenida"
        else:
            s.trayectoria = "estable"

    # ---------------- Petición de humano y bot ----------------
    for i in idx_cliente:
        frag = buscar(L.PETICION_HUMANO, norms[i])
        if not frag:
            continue
        previos = [j for j in idx_empresa if j < i]
        if previos and turnos[previos[-1]].rol == "agente":
            continue  # ya habla con una persona
        s.peticiones_humano.append(_ev(i, "cliente", turnos[i].texto, frag))
    if s.peticiones_humano:
        r = s.peticiones_humano[0].turno - 1
        siguientes = [a for a in idx_agente if a > r]
        s.humano_atendido = bool(siguientes)
        hasta = siguientes[0] if siguientes else len(turnos)
        s.pasos_bot_hasta_humano = sum(1 for b in idx_bot if r < b < hasta) if siguientes else None

    if hubo_bot:
        primeros_bot = idx_bot[:2]
        s.bot_se_identifica = any(buscar(L.BOT_SE_IDENTIFICA, norms[b]) for b in primeros_bot)
        s.bot_ofrece_humano = any(buscar(L.BOT_OFRECE_HUMANO, norms[b]) for b in idx_bot)
        for a_pos, a in enumerate(idx_bot):
            if len(palabras(norms[a])) < 4:
                continue
            for b in idx_bot[a_pos + 1:]:
                if jaccard(norms[a], norms[b]) >= 0.85:
                    s.bucles_bot.append(_ev(b, "bot", turnos[b].texto))
                    break
            frag = buscar(L.FALLBACK_BOT, norms[a])
            if frag:
                s.fallbacks_bot.append(_ev(a, "bot", turnos[a].texto, frag))
        # deduplicar bucles por turno
        vistos_t = set()
        s.bucles_bot = [e for e in s.bucles_bot if not (e.turno in vistos_t or vistos_t.add(e.turno))]
        for a in idx_bot:  # fallbacks cortos también cuentan
            if len(palabras(norms[a])) < 4 and buscar(L.FALLBACK_BOT, norms[a]):
                s.fallbacks_bot.append(_ev(a, "bot", turnos[a].texto))

    # ---------------- Datos pedidos de nuevo (pérdida de contexto) ----------------
    dados: dict[str, tuple[int, str]] = {}  # tipo -> (turno donde se dio, rol que lo pidió)
    pendientes: dict[str, str] = {}
    for i, t in enumerate(turnos):
        n = norms[i]
        if t.rol in EMPRESA:
            if buscar(L.TRANSFERENCIA, n):
                s.transferencias.append(_ev(i, t.rol, t.texto, buscar(L.TRANSFERENCIA, n)))
            for tipo, patrones in L.DATOS.items():
                m = next((x for p in patrones if (x := p.search(n))), None)
                if not m:
                    continue
                s.datos_personales_pedidos = s.datos_personales_pedidos or t.rol == "agente" or t.rol == "bot"
                if tipo in dados:
                    dado_en, rol_pidio = dados[tipo]
                    hubo_transfer = any(dado_en < (e.turno - 1) < i for e in s.transferencias)
                    if rol_pidio != t.rol or hubo_transfer:
                        s.datos_repedidos.append(_ev(i, t.rol, t.texto, m.group(0)))
                pendientes[tipo] = t.rol
        elif t.rol == "cliente" and pendientes:
            for tipo in list(pendientes):
                if _DATO_DADO[tipo](n, t.texto):
                    dados.setdefault(tipo, (i, pendientes[tipo]))
                    pendientes.pop(tipo)
    if hubo_bot and hubo_agente:
        primer_agente = idx_agente[0]
        for a in idx_agente[:3]:
            frag = buscar(L.CONTEXTO_RECONOCIDO, norms[a])
            if frag and a >= primer_agente:
                s.contexto_reconocido = _ev(a, "agente", turnos[a].texto, frag)
                break

    # ---------------- Esfuerzo ----------------
    for i in idx_empresa:
        n, t = norms[i], turnos[i]
        frag = buscar(L.ESPERA, n)
        if frag:
            s.esperas.append(_ev(i, t.rol, t.texto, frag))
        frag = buscar(L.REDIRECCION, n)
        if frag:
            s.redirecciones.append(_ev(i, t.rol, t.texto, frag))

    # ---------------- Radicado, plazo y resolución ----------------
    for i in idx_empresa:
        n, t = norms[i], turnos[i]
        if s.radicado is None:
            frag = buscar(L.RADICADO, n)
            if frag:
                s.radicado = _ev(i, t.rol, t.texto, frag)
        if s.plazo is None:
            frag = buscar(L.PLAZO, n)
            if frag:
                s.plazo = _ev(i, t.rol, t.texto, frag)

    ultimos_cliente = idx_cliente[-3:]
    no_res_cli = next(((i, f) for i in reversed(ultimos_cliente) if (f := buscar(L.NO_RESUELTO_CLIENTE, norms[i]))), None)
    res_emp = next(((i, f) for i in reversed(idx_empresa) if (f := buscar(L.RESUELTO_EMPRESA, norms[i]))), None)
    res_cli = next(((i, f) for i in reversed(idx_cliente) if (f := buscar(L.RESUELTO_CLIENTE, norms[i]))), None)
    cortesia_final = bool(ultimos_cliente) and bool(
        buscar(L.POSITIVO_CLIENTE, norms[ultimos_cliente[-1]]) or buscar(L.ACUSE_CLIENTE, norms[ultimos_cliente[-1]]))
    no_res_emp = next(((i, f) for i in idx_empresa if (f := buscar(L.NO_RESUELTO_EMPRESA, norms[i]))), None)
    # Un "ya quedó" de la empresa que el cliente desmiente después no cuenta.
    if no_res_cli and (res_emp is None or no_res_cli[0] > res_emp[0]):
        s.resolucion = "no_resuelto"
        s.evidencia_resolucion.append(_ev(no_res_cli[0], "cliente", turnos[no_res_cli[0]].texto, no_res_cli[1]))
    elif conv.tipo == "cancelacion" and s.radicado:
        s.resolucion = "resuelto"  # en una cancelación, radicarla es cumplir la solicitud
        s.evidencia_resolucion.append(s.radicado)
    elif conv.tipo == "cancelacion" and not res_emp:
        s.resolucion = "no_resuelto"
    elif res_emp or res_cli:
        s.resolucion = "resuelto"
        for x in (res_emp, res_cli):
            if x:
                s.evidencia_resolucion.append(_ev(x[0], turnos[x[0]].rol, turnos[x[0]].texto, x[1]))
    elif s.radicado:
        s.resolucion = "en_tramite"
        s.evidencia_resolucion.append(s.radicado)
    elif conv.tipo == "ventas" and (s.venta_cerrada or buscar(L.VENTA_CERRADA, " ".join(norms[i] for i in idx_empresa))):
        s.resolucion = "resuelto"
    elif no_res_emp or s.redirecciones:
        s.resolucion = "no_resuelto"
        if not no_res_emp:
            no_res_emp = (s.redirecciones[0].turno - 1, None)
        s.evidencia_resolucion.append(_ev(no_res_emp[0], turnos[no_res_emp[0]].rol, turnos[no_res_emp[0]].texto, no_res_emp[1]))
    elif cortesia_final and s.frustracion_max < 3 and not s.queja:
        s.resolucion = "resuelto"
        u = ultimos_cliente[-1]
        s.evidencia_resolucion.append(_ev(u, "cliente", turnos[u].texto))
    else:
        s.resolucion = "incierto"

    # Sin respuesta: el cliente escribió y nadie de la empresa contestó después.
    if idx_cliente and not any(i > idx_cliente[0] for i in idx_empresa):
        s.sin_respuesta = _ev(idx_cliente[0], "cliente", turnos[idx_cliente[0]].texto)

    # Abandono: el cliente se va sin respuesta útil (último turno es suyo y está frustrado o pidiendo humano).
    if turnos and turnos[-1].rol == "cliente":
        ultimo = norms[-1]
        if (s.frustracion and s.frustracion[-1] >= 3) or buscar(L.PETICION_HUMANO, ultimo):
            s.abandono = True
    if hubo_bot and not hubo_agente and s.peticiones_humano:
        s.abandono = True

    # ---------------- Guion ----------------
    def primero(patrones, indices) -> Evidencia | None:
        for i in indices:
            frag = buscar(patrones, norms[i])
            if frag:
                return _ev(i, turnos[i].rol, turnos[i].texto, frag)
        return None

    atendientes = idx_agente if hubo_agente else idx_bot
    mitad = len(turnos) // 2
    s.guion = {
        "saludo": primero(L.SALUDO, idx_empresa[:3]),
        "identificacion": primero(L.IDENTIFICACION_AGENTE, idx_agente[:3]) if hubo_agente else primero(L.BOT_SE_IDENTIFICA, idx_bot[:2]),
        "aviso_grabacion": primero(L.AVISO_GRABACION, idx_empresa[:4]),
        "indagacion": primero(L.INDAGACION, [i for i in idx_empresa if turnos[i].rol != "sistema"]),
        "resumen": primero(L.RESUMEN, [i for i in atendientes if i >= mitad]),
        "ayuda_adicional": primero(L.AYUDA_ADICIONAL, atendientes[-4:]),
        "despedida": primero(L.DESPEDIDA, idx_empresa[-3:]),
    }
    info = primero(L.INFO_SENSIBLE_CUENTA, idx_empresa)
    if info:
        s.info_cuenta = info
        verif = primero(L.VERIFICACION, idx_empresa)
        s.verificacion_antes_de_info = bool(verif and verif.turno <= info.turno) or (
            "documento" in dados and dados["documento"][0] < info.turno - 1
        )

    # ---------------- Trato ----------------
    for i in idx_empresa:
        if turnos[i].rol == "sistema":
            continue
        n, t = norms[i], turnos[i]
        for patrones, destino in (
            (L.VALIDACION, s.validacion), (L.PARAFRASEO, s.parafraseo), (L.APROPIACION, s.apropiacion),
            (L.CULPA_EVASION, s.culpa_evasion), (L.IRRESPETO_AGENTE, s.irrespeto_agente),
        ):
            frag = buscar(patrones, n)
            if frag:
                destino.append(_ev(i, t.rol, t.texto, frag))
        if t.rol == "agente":
            frag = buscar(L.INSULTOS, n)
            if frag:
                s.irrespeto_agente.append(_ev(i, t.rol, t.texto, frag))
        frag = buscar(L.NEGATIVO_SIN_ALTERNATIVA, n)
        if frag and not buscar(L.ALTERNATIVA, n):
            s.negativo_sin_alternativa.append(_ev(i, t.rol, t.texto, frag))
        s.disculpas_guion += contar(L.DISCULPA_GUION, n)

    # ---------------- Ventas ----------------
    for i in idx_empresa:
        n, t = norms[i], turnos[i]
        for nombre, patrones in (
            ("venta_cerrada", L.VENTA_CERRADA), ("precio", L.PRECIO), ("condiciones", L.CONDICIONES),
            ("retracto", L.RETRACTO), ("autorizacion_datos", L.AUTORIZACION_DATOS),
        ):
            if getattr(s, nombre) is None:
                frag = buscar(patrones, n)
                if frag:
                    setattr(s, nombre, _ev(i, t.rol, t.texto, frag))
        if s.aceptacion is None and buscar(L.PREGUNTA_ACEPTACION, n):
            sig = next((c for c in idx_cliente if c > i), None)
            if (sig is not None and buscar(L.ACEPTACION_CLIENTE, norms[sig]) and not buscar(L.RECHAZO_CLIENTE, norms[sig])
                    and not buscar(L.ACEPTACION_DEBIL, norms[sig])):
                s.aceptacion = _ev(sig, "cliente", turnos[sig].texto)
    if len(s.rechazos_cliente) >= 2:
        segundo = s.rechazos_cliente[1].turno - 1
        for i in idx_empresa:
            if i > segundo:
                frag = buscar(L.OFERTA, norms[i])
                if frag:
                    s.insistencia_tras_rechazo.append(_ev(i, turnos[i].rol, turnos[i].texto, frag))

    # ---------------- Cancelación ----------------
    if conv.tipo == "cancelacion":
        rad = s.radicado.turno - 1 if s.radicado else None
        for i in idx_empresa:
            frag = buscar(L.OFERTA, norms[i])
            if frag:
                ev = _ev(i, turnos[i].rol, turnos[i].texto, frag)
                s.ofertas_en_cancelacion.append(ev)
                if s.retencion_antes_de_radicar is None and (rad is None or i < rad):
                    s.retencion_antes_de_radicar = ev

    # ---------------- Cobranza y seguridad ----------------
    for i in idx_empresa:
        n, t = norms[i], turnos[i]
        frag = buscar(L.COERCION_COBRANZA, n)
        if frag:
            s.coercion.append(_ev(i, t.rol, t.texto, frag))
        frag = buscar(L.PIDE_CREDENCIAL, n)
        if frag and not buscar(L.NEGACION_CREDENCIAL, n):
            s.pide_credencial.append(_ev(i, t.rol, t.texto, frag))
        for m in re.finditer(r"(?:\d[ -]?){13,19}", t.texto):
            if luhn_valido(m.group(0)):
                s.datos_expuestos.append(Evidencia(turno=i + 1, rol=t.rol, cita="(número de tarjeta completo dicho por la empresa)"))
                break

    if conv.direccion == "saliente" and conv.tipo in ("ventas", "cobranza") and conv.inicio is not None:
        s.ventana_legal = ventana_ley_2300(conv.inicio)

    # ---------------- Temas ----------------
    texto_cliente = " ".join(norms[i] for i in idx_cliente)
    s.temas = [tema for tema, pats in L.TEMAS.items() if buscar(pats, texto_cliente)]
    if conv.tipo == "cancelacion" and "cancelacion" not in s.temas:
        s.temas.append("cancelacion")

    # ---------------- Índices compuestos ----------------
    bucle = bool(s.bucles_bot) or len(s.fallbacks_bot) >= 2
    s.esfuerzo = min(10, (
        2 * sum(1 for e in s.transferencias if e.rol != "bot") + len(s.esperas) + 2 * len(s.redirecciones) + 2 * len(s.datos_repedidos)
        + (2 if bucle else 0) + (3 if s.humano_atendido is False else 0) + len(s.repeticiones_cliente)
    ))
    if hubo_agente:
        intensos = sum(1 for f in s.frustracion if f >= 5)
        s.carga_emocional = min(100, 25 * len(s.insultos_cliente) + 10 * len(s.amenazas_externas) + 8 * intensos
                                + (10 if s.trayectoria == "escalada" else 0))
    return s
