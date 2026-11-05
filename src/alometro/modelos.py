"""Modelos de datos de Alómetro.

Todo es `dataclass` de la biblioteca estándar: sin dependencias, para que el
motor funcione igual en un servidor, en un portátil sin internet o dentro del
navegador (Pyodide).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

ROLES = ("cliente", "agente", "bot", "sistema")
TIPOS = ("ventas", "servicio", "soporte", "cobranza", "retencion", "cancelacion")
CANALES = ("voz", "chat", "whatsapp", "correo", "redes")
DIRECCIONES = ("entrante", "saliente")
SECTORES = ("general", "telecom", "financiero", "salud", "servicios_publicos", "comercio", "seguros")

# Sinónimos aceptados al cargar datos de otros sistemas.
_ROL_ALIAS = {
    "customer": "cliente", "client": "cliente", "usuario": "cliente", "user": "cliente",
    "caller": "cliente", "consumidor": "cliente",
    "agent": "agente", "asesor": "agente", "asesora": "agente", "operador": "agente",
    "operadora": "agente", "humano": "agente", "human": "agente", "representante": "agente",
    "assistant": "bot", "chatbot": "bot", "ia": "bot", "ai": "bot", "virtual": "bot",
    "asistente": "bot", "ivr": "sistema", "system": "sistema", "sys": "sistema",
}


def normalizar_rol(rol: str) -> str:
    r = (rol or "").strip().lower()
    r = _ROL_ALIAS.get(r, r)
    if r not in ROLES:
        raise ValueError(f"Rol desconocido: {rol!r}. Usa uno de {ROLES}.")
    return r


@dataclass
class Turno:
    rol: str
    texto: str
    t: float | None = None  # segundos desde el inicio (opcional)

    def __post_init__(self) -> None:
        self.rol = normalizar_rol(self.rol)
        self.texto = (self.texto or "").strip()


@dataclass
class Conversacion:
    id: str
    turnos: list[Turno]
    tipo: str = "servicio"
    canal: str = "voz"
    sector: str = "general"
    direccion: str | None = None
    inicio: datetime | None = None
    cliente_id: str | None = None
    agente_id: str | None = None
    csat: float | None = None
    metadatos: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tipo = (self.tipo or "servicio").strip().lower()
        if self.tipo not in TIPOS:
            raise ValueError(f"Tipo desconocido: {self.tipo!r}. Usa uno de {TIPOS}.")
        self.canal = (self.canal or "voz").strip().lower()
        self.sector = (self.sector or "general").strip().lower()
        if self.direccion is None:
            # Ventas y cobranza suelen ser llamadas que hace la empresa.
            self.direccion = "saliente" if self.tipo in ("ventas", "cobranza") else "entrante"
        self.direccion = self.direccion.strip().lower()
        if self.direccion not in DIRECCIONES:
            raise ValueError(f"Dirección desconocida: {self.direccion!r}. Usa {DIRECCIONES}.")

    @property
    def hubo_bot(self) -> bool:
        return any(t.rol == "bot" for t in self.turnos)

    @property
    def hubo_agente(self) -> bool:
        return any(t.rol == "agente" for t in self.turnos)


@dataclass
class Evidencia:
    """Cita textual que respalda un hallazgo. `turno` es 1-based para lectura humana."""

    turno: int
    rol: str
    cita: str

    def a_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResultadoCriterio:
    id: str
    nombre: str
    dimension: str
    peso: int
    critico: str | None  # "cliente" | "negocio" | "cumplimiento" | None
    aplica: bool
    cumple: bool | None
    detalle: str = ""
    evidencias: list[Evidencia] = field(default_factory=list)
    recomendacion: str = ""

    def a_dict(self) -> dict:
        d = asdict(self)
        d["evidencias"] = [e.a_dict() for e in self.evidencias]
        return d


@dataclass
class Evaluacion:
    conversacion_id: str
    tipo: str
    canal: str
    sector: str
    direccion: str
    agente_id: str | None
    cliente_id: str | None
    inicio: str | None
    puntaje_base: int  # 0-100 sobre criterios no críticos aplicables
    puntaje: int  # puntaje final (0 si hay error crítico y la política lo anula)
    nivel: str
    errores_criticos: list[dict]
    criterios: list[ResultadoCriterio]
    senales: dict[str, Any]
    dimensiones: dict[str, int | None]
    recomendaciones: list[str]

    def a_dict(self) -> dict:
        d = asdict(self)
        d["criterios"] = [c.a_dict() for c in self.criterios]
        return d
