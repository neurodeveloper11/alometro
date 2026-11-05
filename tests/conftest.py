from datetime import datetime

import pytest

from alometro.calendario import HORA_COLOMBIA
from alometro.modelos import Conversacion, Turno


def conv(turnos, **kw):
    """Atajo: conv([("cliente", "hola"), ("agente", "...")], tipo="servicio")."""
    kw.setdefault("id", "t-1")
    return Conversacion(turnos=[Turno(rol=r, texto=t) for r, t in turnos], **kw)


@pytest.fixture
def lunes_10am():
    return datetime(2026, 10, 13, 10, 0, tzinfo=HORA_COLOMBIA)
