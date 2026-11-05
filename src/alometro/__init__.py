"""Alómetro: evaluación objetiva de la calidad de atención en call centers y chatbots.

Uso rápido::

    from alometro import cargar, evaluar, calcular_indicadores
    convs = cargar("conversaciones.jsonl")
    evaluaciones = [evaluar(c) for c in convs]
    resumen = calcular_indicadores(evaluaciones)
"""

from .cargar import cargar, desde_dict, desde_txt
from .detectores import analizar
from .indicadores import calcular as calcular_indicadores
from .indicadores import comparar
from .modelos import Conversacion, Evaluacion, Turno
from .motor import Politica, evaluar, evaluar_lote
from .rubrica import CRITERIOS

__version__ = "0.1.0"
__all__ = [
    "CRITERIOS",
    "Conversacion",
    "Evaluacion",
    "Politica",
    "Turno",
    "__version__",
    "analizar",
    "calcular_indicadores",
    "cargar",
    "comparar",
    "desde_dict",
    "desde_txt",
    "evaluar",
    "evaluar_lote",
]
