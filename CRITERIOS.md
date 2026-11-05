# Criterios y metas de Alómetro

> Archivo generado por `scripts/generar_criterios_md.py` a partir de `src/alometro/rubrica.py` e `indicadores.py`. No editar a mano.

## Cómo se calcula la nota

* Cada criterio declara **cuándo aplica**, **qué es cumplir** y **qué evidencia** lo respalda (turno y cita).
* Nota base = 100 × puntos de los criterios cumplidos / puntos de los criterios que aplican. Lo que no aplica no suma ni resta.
* Los **errores críticos** (peso 0, marcados ⛔) se cuentan aparte en tres categorías: *cliente*, *negocio* y *cumplimiento*.
  Por defecto anulan la nota de la interacción (nivel «Crítico»). Se puede desactivar con `--no-anular`.
* Niveles: Excelente ≥ 90 · Bueno ≥ 75 · Mejorable ≥ 60 · Deficiente < 60 · Crítico = hay error crítico.

## Criterios de revisión (por interacción)

### Resolución

| Id | Criterio | Peso | Qué hacer si falla | Fundamento |
|---|---|---|---|---|
| R1 | Resuelve o deja trámite formal | 20 | Cierre cada contacto con una solución confirmada o con un radicado y un plazo concretos. | Resolución en el primer contacto (FCR): evita el recontacto, que es costo para la empresa y esfuerzo para el cliente. |
| R2 | Radicado y plazo ante queja | 10 | Ante toda queja o reclamo entregue el número de radicado (CUN en telecomunicaciones) y el plazo legal de respuesta. | En telecomunicaciones la PQR se identifica con CUN y el operador tiene 15 días hábiles; en general la queja debe quedar trazable. |
| R3 | Sin callejón sin salida | ⛔ crítico (cliente) | Si no puede resolver, nunca termine sin un siguiente paso: radique, escale o agende. | Un cliente sin solución ni camino convierte su caso en PQR, en queja ante la SIC o la CRC, o en abandono. |

### Esfuerzo del cliente

| Id | Criterio | Peso | Qué hacer si falla | Fundamento |
|---|---|---|---|---|
| E1 | Máximo una transferencia | 8 | Resuelva o transfiera una sola vez, con el caso documentado. | Cada transferencia obliga a repetir el caso y aumenta el esfuerzo del cliente (CES). |
| E2 | No pide datos ya entregados | 10 | Lea el historial y lo que el cliente ya dio antes de pedirle datos. | Escalar a una persona sin perder el contexto es la función más valorada de un chatbot bancario en Colombia (63 %, Delto 2025). |
| E3 | No manda a otro canal sin resolver | 6 | Si otro canal es necesario, deje radicado el caso antes de enviarlo allí. | Desviar al cliente («escriba al correo», «vaya a una oficina») traslada el esfuerzo al cliente. |
| E4 | Esperas razonables | 4 | Agrupe las consultas internas para no poner al cliente en espera varias veces. | Varias esperas seguidas indican que quien atiende no tiene la información a mano y alargan el contacto. |
| E5 | El cliente no repite su mensaje | 5 | Si el cliente repite algo, es señal de que no se le entendió: confirme y cambie de enfoque. | La repetición es un indicador directo de comprensión fallida. |
| E6 | Esfuerzo total bajo | 5 | Revise el recorrido completo: cada obstáculo suma (transferencia, espera, desvío, bucle, dato repetido). | Índice de esfuerzo 0-10 de Alómetro, inspirado en el Customer Effort Score (CES). |

### Trato humano

| Id | Criterio | Peso | Qué hacer si falla | Fundamento |
|---|---|---|---|---|
| T1 | Reconoce la emoción del cliente | 10 | Nombre la emoción antes de la solución: «Entiendo su molestia, llevar tres días sin servicio es mucho». | Validación emocional: reduce la activación y abre la escucha (base de la desescalada). |
| T2 | Escucha activa | 6 | Parafrasee la solicitud: «Si le entiendo bien, el cobro de octubre no corresponde…». | Parafrasear confirma comprensión y evita resolver el problema equivocado. |
| T3 | Se hace cargo del caso | 5 | Use lenguaje de responsabilidad: «Yo me encargo», «Voy a revisar…». | El lenguaje de apropiación aumenta la confianza en la solución. |
| T4 | Sin culpar ni negar sin alternativa | 8 | Cambie «no se puede» por «lo que sí puedo hacer es…» y nunca culpe al cliente. | Las negativas secas y la culpa al cliente disparan la frustración. |
| T5 | Trato respetuoso | ⛔ crítico (cliente) | Tolerancia cero al irrespeto. Si el cliente agrede, aplique el protocolo de llamada difícil. | El irrespeto al cliente es un error crítico en cualquier modelo de calidad. |
| T6 | Baja la frustración | 8 | Valide, explique qué va a hacer y en cuánto tiempo, y confirme al final. | El estado emocional con el que termina la conversación es lo que el cliente recuerda de la marca. |
| T7 | Empatía real, no de plantilla | 3 | Evite repetir «lamentamos los inconvenientes»: personalice la disculpa una sola vez. | La disculpa repetida de guion se percibe como indiferencia. |

### Asistente virtual

| Id | Criterio | Peso | Qué hacer si falla | Fundamento |
|---|---|---|---|---|
| B1 | El asistente dice que es virtual | 5 | Configure el primer mensaje: «Soy el asistente virtual de…; si lo prefiere, le paso con una persona». | Transparencia: los proyectos de ley de IA en Colombia piden avisar cuando se habla con una IA. |
| B2 | Pasa a una persona cuando se pide | 12 | Transfiera a una persona como máximo en la segunda respuesta después de que la pidan. | El 60 % de los clientes teme que la IA le impida llegar a una persona (Gartner, encuesta a 5.728 clientes, 2024). |
| B2C | No niega la atención humana | ⛔ crítico (cliente) | Nunca bloquee la salida a humano: la petición repetida debe forzar el traspaso. | La preferencia por la atención humana es el motivo más citado para abandonar los chatbots bancarios en Colombia (39 %, Delto 2025). |
| B3 | Sin bucles del bot | 10 | Tras dos «no entendí» seguidos, ofrezca una persona automáticamente. | El «bucle sin salida» (doom loop) infla la contención y destruye la satisfacción. |
| B4 | Traspaso con contexto | 8 | Pase a la persona la intención, los datos verificados y lo ya intentado. | Escalar a un humano sin perder el contexto es la función más valorada de un chatbot bancario (63 %, Delto 2025). |
| B5 | Contención real, no falsa | ⛔ crítico (cliente) | Mida la contención solo cuando el cliente resolvió; si no, debe salir a una persona. | Un bot que «retiene» clientes sin resolverles es una contención falsa: el problema vuelve por otro canal. |

### Proceso y guion

| Id | Criterio | Peso | Qué hacer si falla | Fundamento |
|---|---|---|---|---|
| P1 | Saludo | 2 | Salude al iniciar. | Protocolo básico de apertura. |
| P2 | Identificación de quien atiende | 3 | Diga su nombre y la empresa (o que es un asistente virtual). | El cliente debe saber con quién habla. |
| P3 | Indaga la necesidad | 4 | Pregunte de forma abierta y deje que el cliente explique. | Sin diagnóstico no hay solución correcta. |
| P4 | Verifica identidad antes de dar datos | 8 | Valide la identidad antes de dar saldos, deudas o datos de la cuenta. | Protección de datos personales y prevención de fraude. |
| P5 | Resume lo acordado | 4 | Antes de cerrar, resuma: qué se hizo, qué sigue y cuándo. | El resumen reduce el recontacto por malentendidos. |
| P6 | Ofrece ayuda adicional | 2 | Pregunte si hay algo más. | Cierre completo. |
| P7 | Despedida cordial | 2 | Despídase con cordialidad. | Protocolo de cierre. |
| P8 | Aviso de grabación | 3 | Informe al inicio que la llamada se graba y para qué. | Transparencia en el tratamiento de datos (Ley 1581 de 2012). |

### Cumplimiento (Colombia)

| Id | Criterio | Peso | Qué hacer si falla | Fundamento |
|---|---|---|---|---|
| L1 | Horario legal de contacto | ⛔ crítico (cumplimiento) | Programe las campañas salientes solo de lunes a viernes de 7:00 a 19:00 y sábados de 8:00 a 15:00, sin domingos ni festivos. | Ley 2300 de 2023 («Dejen de fregar»), art. 3. |
| L2 | Informa el derecho de retracto | ⛔ crítico (cumplimiento) | En toda venta telefónica o digital informe los 5 días hábiles para retractarse. | Ley 1480 de 2011 (Estatuto del Consumidor), art. 47; Decreto 1074 de 2015. |
| L3 | Aceptación expresa de la venta | ⛔ crítico (negocio) | Pregunte «¿Acepta…?» y espere un «sí, acepto» claro antes de activar. | Sin aceptación expresa la venta es reversible y genera reclamos por cobros no autorizados. |
| L4 | Precio y condiciones claros | 8 | Diga el precio total, la permanencia y cuándo cambia el precio promocional. | Información clara, veraz y suficiente (Ley 1480 de 2011). |
| L5 | Autorización de datos personales | 6 | Pida autorización de tratamiento de datos antes de registrar datos personales. | Ley 1581 de 2012 (Habeas Data). |
| L6 | Respeta el «no» del cliente | 8 | Tras dos negativas, agradezca y cierre. | La insistencia tras una negativa es la práctica que la Ley 2300 de 2023 («Dejen de fregar») busca frenar. |
| L7 | Cancelación sin trabas | ⛔ crítico (cumplimiento) | Radique primero la cancelación y entregue el número; cualquier oferta, después y por otro canal. | Res. CRC 8171 de 2026 (servicios móviles): canal de cancelación sin ofertas de retención y con envío del CUN. |
| L8 | Cobranza sin coerción | ⛔ crítico (cumplimiento) | Nunca amenace ni mencione a terceros, visitas o consecuencias penales. | Ley 2300 de 2023: prohíbe visitas al domicilio o trabajo y contactar a terceros; prácticas abusivas de cobranza. |
| L9 | Nunca pide claves ni códigos | ⛔ crítico (negocio) | Nunca pida clave, PIN, CVV ni códigos OTP: diga «nunca se los pediremos». | Es la puerta de entrada del fraude por suplantación (vishing). |

## Criterios de resultado (¿se está logrando el objetivo?)

Se calculan sobre el conjunto de interacciones, con intervalo de confianza del 95 % (Wilson).
Las metas son **puntos de partida**; fíjelas con 4 semanas de línea base de su operación.

| Id | Indicador | Fórmula | Meta | Por qué importa |
|---|---|---|---|---|
| I01 | Resolución en el contacto | resueltas o radicadas con plazo / interacciones de atención | ≥ 70 % | Es el objetivo principal: que el cliente salga con su problema resuelto o con un compromiso concreto. |
| I02 | Recontacto en 7 días | clientes que vuelven a contactar en 7 días / interacciones observables | ≤ 15 % | La prueba real de la resolución: si el cliente vuelve, no se resolvió (aunque la conversación lo pareciera). |
| I03 | Peticiones de humano atendidas | transferidas a una persona / conversaciones de bot donde se pidió | ≥ 95 % | Responde a la queja central de la gente: «quiero hablar con una persona». |
| I04 | Respuestas del bot hasta la persona | mediana de respuestas del bot entre la petición y la persona | ≤ 2 pasos | Cada respuesta extra del bot después de pedir una persona aumenta la frustración. |
| I05 | Bucles del bot | conversaciones con bucle / conversaciones con bot | ≤ 5 % | El bucle sin salida es la experiencia que hace sentir que «el servicio al cliente no sirve». |
| I06 | Contención falsa | conversaciones solo-bot sin solución o con recontacto / conversaciones solo-bot | ≤ 10 % | Separa la contención real (el bot resolvió) de la aparente (el cliente se rindió o volvió por otro canal). |
| I07 | Pérdida de contexto | conversaciones donde se repidieron datos / conversaciones con traspaso | ≤ 10 % | Escalar sin perder el contexto es lo que más valoran los usuarios de chatbots bancarios en Colombia (63 %, Delto 2025). |
| I08 | Desescalada de clientes frustrados | clientes que terminan menos frustrados / clientes que empezaron frustrados | ≥ 60 % | Mide si la atención calma o enciende. Es la competencia humana que un bot no reemplaza. |
| I09 | Frustración que escala | conversaciones donde la frustración sube / conversaciones con 2+ turnos del cliente | ≤ 10 % | La conversación no debería empeorar el ánimo del cliente. |
| I10 | Libre de error crítico: cliente | interacciones sin error crítico de cliente / total | ≥ 95 % | Callejón sin salida, humano negado, irrespeto o contención falsa. |
| I11 | Libre de error crítico: negocio | interacciones sin error crítico de negocio / total | ≥ 97 % | Ventas sin aceptación expresa, petición de claves u OTP. |
| I12 | Libre de error crítico: cumplimiento | interacciones sin error crítico normativo / total | ≥ 99 % | Ley 2300, Ley 1480, Res. CRC 8171: cada falla es una posible sanción. |
| I13 | Esfuerzo alto del cliente | interacciones con esfuerzo ≥ 5 de 10 / total | ≤ 15 % | Transferencias, esperas, desvíos y repeticiones. El esfuerzo del cliente se asocia con la deslealtad (Dixon, Freeman y Toman, HBR 2010). |
| I14 | Amenaza de queja externa | interacciones con mención de SIC, tutela, abogado o redes / total | ≤ 3 % | Anticipa quejas ante la SIC, la Superfinanciera o la CRC y crisis en redes. |
| I15 | Abandono sin solución | interacciones donde el cliente se va frustrado o pidiendo humano / total | ≤ 5 % | El cliente que se va sin solución no siempre se queja: simplemente se va. |
| I16 | Puntaje de calidad promedio | promedio del puntaje final (0-100) | ≥ 80 pts | Resume el cumplimiento de la rúbrica, con los errores críticos anulando la nota. |

## Criterios para verificar que la herramienta mide bien

| Verificación | Cómo | Umbral |
|---|---|---|
| Acuerdo con analistas humanos | `alometro calibrar` (kappa de Cohen por criterio, ≥ 50 interacciones doble-calificadas) | κ ≥ 0,60 y n ≥ 20 por criterio para usarlo en decisiones |
| Precisión de los detectores | `python eval/evaluar.py` sobre conjuntos escritos a mano, incluido uno ciego | Reportar siempre la cifra del conjunto ciego |
| Validez frente al cliente | Correlación de Spearman entre el puntaje y la encuesta CSAT | ρ > 0 y creciente en el tiempo |
| Validez frente al resultado | Recontacto a 7 días de las interacciones «resueltas» vs. «no resueltas» | Recontacto menor en las «resueltas» |
| Mejora real, no ruido | `alometro comparar antes despues` (IC 95 % y p-valor por indicador) | p < 0,05 en la dirección deseada |
