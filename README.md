# Alómetro

**Mide lo que pasa en cada llamada.** Alómetro evalúa conversaciones de call center y de chatbots (voz transcrita, chat, WhatsApp) con criterios objetivos y auditables, pensados para Colombia y Latinoamérica. Revisa si el cliente **resolvió**, cuánto **esfuerzo** le costó, si el bot lo **dejó llegar a una persona**, cómo terminó su **emoción** y si la atención **cumplió la ley**.

* 100 % local: no envía nada a internet ni usa APIs externas. Funciona en un servidor, en un portátil o en el navegador.
* Sin dependencias: Python 3.10+ y la biblioteca estándar.
* Auditable: cada hallazgo cita el turno y la frase que lo respalda. Las evidencias se anonimizan.
* Medible: indicadores de resultado con meta e intervalo de confianza, comparación antes/después con significancia estadística y calibración contra analistas humanos (kappa).

> **Aviso.** Alómetro es una herramienta de apoyo a la calidad. No reemplaza la revisión humana ni la asesoría jurídica. Los criterios normativos resumen la Ley 2300 de 2023, la Ley 1480 de 2011, la Ley 1581 de 2012 y resoluciones de la CRC; verifique el texto vigente antes de usarlos en auditorías o contratos.

## Por qué

En Colombia, la queja más repetida sobre el servicio al cliente es que *no sirve*: bots que no entienden y no dejan hablar con una persona, traspasos donde hay que volver a dictar la cédula, «llame más tarde», cancelaciones llenas de trabas y llamadas de cobranza a cualquier hora. Las métricas tradicionales (tiempo de atención, «contención» del bot) no ven nada de eso. El 64 % de los clientes preferiría que las empresas no usaran IA en el servicio, y su principal miedo es no poder llegar a una persona ([Gartner, 2024](https://www.gartner.com/en/newsroom/press-releases/2024-07-09-gartner-survey-finds-64-percent-of-customers-would-prefer-that-companies-didnt-use-ai-for-customer-service)). Más contexto en [INVESTIGACION.md](INVESTIGACION.md).

## Qué evalúa

**39 criterios en 6 dimensiones**: Resolución, Esfuerzo del cliente, Trato humano, Asistente virtual, Proceso y guion, y Cumplimiento (Colombia). Incluye **10 errores críticos** que anulan la nota: callejón sin salida, atención humana negada, contención falsa, irrespeto, contacto fuera del horario de la Ley 2300, venta sin retracto o sin aceptación expresa, retención antes de radicar una cancelación, cobranza coercitiva y petición de claves u OTP.

Sobre el conjunto de interacciones calcula **16 indicadores de resultado**, entre ellos: resolución, recontacto a 7 días, peticiones de humano atendidas, bucles del bot, contención falsa frente a real, pérdida de contexto, desescalada emocional, % libre de errores críticos, esfuerzo y amenazas de queja ante la SIC.

Todos los criterios, pesos, metas y fundamentos están en **[CRITERIOS.md](CRITERIOS.md)**.

Sirve para los tres tipos de operación: **ventas** (telemercadeo saliente), **servicio y retención** a clientes actuales (incluida la cancelación y la cobranza) y **soporte y PQR** (líneas de entrada y bots).

## Instalación

```bash
pip install "git+https://github.com/neurodeveloper11/alometro.git"
# opcional: anonimización avanzada con DataShield (cédula, NIT, direcciones colombianas…)
pip install "alometro[privacidad] @ git+https://github.com/neurodeveloper11/alometro.git"
```

## Uso rápido

```bash
alometro demo                                   # datos sintéticos + informes de ejemplo
alometro evaluar conversaciones.jsonl -o informe.html --json resultados.json --csv resultados.csv
alometro comparar enero.jsonl febrero.jsonl     # ¿mejoró de verdad?
alometro calibrar conversaciones.jsonl etiquetas_analistas.csv
alometro criterios                              # imprime la rúbrica
```

```python
from alometro import cargar, evaluar, calcular_indicadores

convs = cargar("conversaciones.jsonl")
evs = [evaluar(c) for c in convs]
resumen = calcular_indicadores(evs)
for ind in resumen["indicadores"]:
    print(ind.nombre, ind.valor, ind.estado)
```

### Formato de entrada

JSONL (una conversación por línea). Los roles son `cliente`, `agente`, `bot` y `sistema` (IVR o avisos):

```json
{"id": "c-001", "tipo": "servicio", "canal": "whatsapp", "sector": "telecom", "direccion": "entrante",
 "inicio": "2026-10-13T10:05:00-05:00", "cliente_id": "h:9f2c", "agente_id": "A17",
 "turnos": [{"rol": "bot", "texto": "Hola, soy el asistente virtual…"},
            {"rol": "cliente", "texto": "Quiero hablar con un asesor"}]}
```

* `tipo`: `ventas`, `servicio`, `soporte`, `cobranza`, `retencion` o `cancelacion`.
* `sector`: `telecom`, `financiero`, `salud`, `servicios_publicos`, `comercio`, `seguros` o `general`. Activa reglas como la de la CRC.
* `inicio`, `cliente_id` y `direccion` habilitan el recontacto a 7 días y las reglas de horario y frecuencia de la Ley 2300.
* También acepta CSV (una fila por turno) y texto plano (`Agente: …` / `Cliente: …`). Ver `src/alometro/cargar.py` y la carpeta `ejemplos/`.

## Cómo verificar que se está logrando el objetivo

1. **Línea base**: evalúe 4 semanas antes de cambiar nada (≈ 385 interacciones por periodo dan ±5 puntos de precisión).
2. **Calibración**: dos analistas califican 50 o más interacciones; `alometro calibrar` da el kappa por criterio. Use para decisiones solo los criterios con κ ≥ 0,60.
3. **Intervención**: corrija lo que el informe señala (flujo del bot, traspaso con contexto, guion de cancelación, coaching por criterio).
4. **Comparación**: `alometro comparar antes.jsonl despues.jsonl` indica para cada indicador si hubo una *mejora significativa*, si *empeoró* o si el cambio *no es concluyente* (IC 95 % y p-valor).
5. **Validez externa**: si tiene encuestas CSAT, `calibrar` calcula la correlación con el puntaje; y el recontacto a 7 días comprueba si lo «resuelto» lo estaba de verdad.

## Precisión: cifras honestas

Los detectores son reglas léxicas explícitas (`src/alometro/lexicos.py`) evaluadas con conjuntos escritos a mano, con redacciones distintas a las de los datos de demostración:

| Conjunto | Uso | Exactitud |
|---|---|---|
| v1 (30 casos) | escrito antes de ajustar; luego se usó para ajustar | 0,77 antes de ajustar |
| v2 ciego (29 casos) | escrito tras el ajuste con v1, antes de volver a tocar el motor | **0,65** (cifra honesta de la v0.1-pre) |
| v3 ciego | ver [`eval/RESULTADOS.md`](eval/RESULTADOS.md) | cifra honesta de la v0.1 |

Son conjuntos pequeños, sintéticos y escritos por el mismo autor de las reglas: sirven para detectar huecos, no como garantía. Por eso cada hallazgo trae evidencia y por eso existe `calibrar`.

## Desarrollo

```bash
pip install -e ".[dev]"
pytest
python eval/evaluar.py eval/casos_v3_ciego.jsonl
python scripts/generar_criterios_md.py   # regenera CRITERIOS.md desde el código
```

Estructura: `detectores.py` (señales con evidencia) → `rubrica.py` (criterios) → `motor.py` (nota) → `indicadores.py` (resultados y comparación) → `informe.py` (HTML). `calendario.py` calcula los festivos colombianos (Ley Emiliani) para la Ley 2300.

## Licencia

MIT. Creado por [Fabio Torres](https://www.linkedin.com/in/fabio-torres-39364b258), ingeniero de datos y psicólogo organizacional.
