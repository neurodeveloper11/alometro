# Evaluación de los detectores

Los detectores de Alómetro son reglas léxicas explícitas (`src/alometro/lexicos.py`). Para saber si generalizan
se usan conjuntos de conversaciones escritas a mano, con redacciones distintas a las de los datos sintéticos de la demo.

## Método

1. Se escribe un conjunto nuevo **antes** de tocar el motor y se mide: esa es la cifra **ciega**, la única que vale como estimación.
2. Se analizan los errores y se corrigen con reglas **generales** (no copiando la frase exacta del caso).
3. Ese conjunto deja de ser ciego: queda como prueba de regresión y la siguiente medición exige un conjunto nuevo.

Se ejecuta con `python eval/evaluar.py eval/casos_<conjunto>.jsonl`. Señales evaluadas: petición de humano, humano atendido,
bucle del bot, pérdida de contexto, resolución, queja, radicado, petición de credenciales, coerción en cobranza, retención
en cancelación, aceptación de venta, amenaza de queja externa, conversación sin respuesta y trayectoria emocional.

## Historial (cifras ciegas, medidas antes de ajustar)

| Conjunto | Casos | Señales | Exactitud | Momento |
|---|---|---|---|---|
| v1 | 30 | 48 | 0,77 | línea base, antes de ajustar |
| v2 ciego | 29 | 40 | 0,65 | tras ajustar con v1 |
| v3 ciego | 31 | 40 | 0,70 | tras las revisiones 1 y 2 |
| **v4 ciego** | 22 | 30 | **0,87** | tras ajustar con v3 — **cifra vigente** |

Después de cada medición se corrigieron los errores; hoy los cuatro conjuntos pasan al 100 %, pero esa cifra **no** mide
la generalización (ya se vieron los casos). La próxima estimación honesta requiere un conjunto v5 nuevo.

## Limitaciones conocidas

* Los conjuntos son pequeños (22-31 casos), sintéticos y escritos por el mismo autor de las reglas: uno o dos casos mueven
  mucho los porcentajes. Sirven para encontrar huecos, no como garantía.
* Las paráfrasis abiertas son el punto débil de cualquier regla léxica: pedir un código OTP sin decir «código»,
  ofertas de retención indirectas, coerción velada. Por eso cada hallazgo trae evidencia para revisión humana.
* Para usar un criterio en decisiones sobre personas, calibre con analistas de su propia operación (`alometro calibrar`,
  κ ≥ 0,60 con al menos 20 casos por criterio).
* Siguiente paso previsto: un clasificador local opcional entrenado con las etiquetas de calibración de cada empresa,
  usado solo como segunda opinión de las reglas.
