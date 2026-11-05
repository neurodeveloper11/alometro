# Investigación: el problema de la atención al cliente en Colombia

Resumen de la investigación que fundamenta la rúbrica de Alómetro (noviembre de 2026).
Las cifras vienen de las fuentes citadas; donde una fuente es secundaria o de un proveedor, se indica.
**Antes de citar una norma en un contrato o una auditoría, verifique el texto oficial vigente.**

## 1. Lo que vive el cliente

| Hallazgo | Fuente |
|---|---|
| El 64 % de los clientes preferiría que las empresas no usaran IA en el servicio al cliente; el 53 % consideraría irse a la competencia. La principal preocupación (≈ 60 %) es que la IA haga más difícil llegar a una persona. | [Gartner, julio 2024](https://www.gartner.com/en/newsroom/press-releases/2024-07-09-gartner-survey-finds-64-percent-of-customers-would-prefer-that-companies-didnt-use-ai-for-customer-service) (5.728 clientes) |
| Colombia, chatbots bancarios: el motivo más citado para abandonarlos es la preferencia por la atención humana (39 %), seguido de malas experiencias (33 %) y consultas demasiado específicas (24 %). La función más valorada: escalar a un humano **sin perder el contexto** (63 %). | [Estudio Delto, agosto 2025](https://www.descubre.vc/noticia/delto-estudio-revela-por-qu-los-colombianos-abandonan-los-chatbots-bancarios-2025-08-11) |
| El 83 % de los consumidores colombianos ya ha interactuado con chatbots o agentes virtuales con IA; esperan que detecten enojo o frustración. | Infobip, «América opina» 2025 (vía [Portafolio](https://www.portafolio.co/tecnologia/como-viene-la-atencion-al-cliente-en-colombia-que-sectores-usan-mas-chatbots-639678)) |
| El 85,2 % de los colombianos dejaría de comprar una marca tras una mala experiencia de servicio; solo el 4,8 % prefiere chatbots. *(Encuesta de HubSpot; fecha no confirmada.)* | [Portafolio](https://www.portafolio.co/negocios/empresas/que-canales-de-atencion-prefieren-los-clientes-colombianos-607305) |
| Telecomunicaciones: 2,01 millones de quejas en el segundo semestre de 2024 (CRC). Entre agosto de 2022 y septiembre de 2025 la SIC recibió 128.321 quejas de usuarios de telecomunicaciones. | [DPL News / CRC](https://dplnews.com/colombia-quejas-por-servicios-de-telecomunicaciones-cayeron-un-267-en-el-segundo-semestre-de-2024-crc/), [Asuntos Legales](https://www.asuntoslegales.com.co/actualidad/superindustria-y-comercio-apela-a-impulsar-el-sector-de-telecomunicaciones-2839603) |
| La SIC ha multado a operadores por no atender PQR o no cumplir decisiones favorables al usuario (p. ej. Claro, $285 millones). | [El Heraldo](https://www.elheraldo.co/economia/la-sic-impone-multa-claro-por-285-millones-884317) |

### Problemas recurrentes (y el criterio de Alómetro que los mide)

1. **El bot no deja llegar a una persona** o lo hace tras muchos pasos → B2, B2C, I03, I04.
2. **Bucles sin salida** («no te entendí», el mismo menú una y otra vez) → B3, I05.
3. **Contención falsa**: el bot «retiene» clientes que en realidad se rinden y vuelven por otro canal → B5, I06.
4. **Pérdida de contexto**: la persona vuelve a pedir la cédula que el cliente ya le dio al bot → E2, B4, I07.
5. **No resolver ni dejar camino**: «llame más tarde», «eso no es conmigo», «acérquese a una oficina» → R1, R3, E3, I01.
6. **Recontacto**: la conversación «parecía» resuelta pero el cliente vuelve → I02 (recontacto a 7 días).
7. **Trabas para cancelar**: ofertas de retención en lugar de radicar → L7.
8. **Telemercadeo y cobranza invasivos**: horarios, insistencia, amenazas, terceros → L1, L6, L8 y alertas de frecuencia.
9. **Fraude por suplantación**: pedir claves, PIN, CVV o códigos OTP → L9.
10. **Trato**: no reconocer la emoción, culpar al cliente, empatía de plantilla → T1-T7.
11. **Agentes desgastados**: el call center tiene alta prevalencia de burnout asociada al clima organizacional ([revisión de 17 estudios, U. de Antioquia, 2023](https://bibliotecadigital.udea.edu.co/handle/10495/40238)) → carga emocional por agente y alerta psicosocial.

## 2. Marco normativo colombiano usado en la rúbrica

| Norma | Qué exige (resumen) | Criterio |
|---|---|---|
| **Ley 2300 de 2023** («Dejen de fregar»), art. 3 | Cobranza (y, por extensión, publicidad y ofertas): lunes a viernes 7:00-19:00, sábados 8:00-15:00, sin domingos ni festivos. Con contacto directo establecido, no más de una vez al día ni por varios canales en la misma semana. Prohíbe visitas al domicilio o lugar de trabajo. | L1, L8, alertas de frecuencia |
| **Ley 1480 de 2011** (Estatuto del Consumidor), arts. 46-47; Decreto 1074 de 2015 | Ventas a distancia: informar identidad, características, precio y **derecho de retracto** (5 días hábiles). | L2, L4 |
| **Ley 1581 de 2012** (Habeas Data) | Autorización previa para el tratamiento de datos personales; transparencia. | L5, P8 |
| **Res. CRC 5050 de 2016 / 5111 de 2017** (Régimen de Protección de Usuarios de Comunicaciones) | PQR por la línea gratuita; CUN; 15 días hábiles de respuesta; silencio administrativo positivo. | R2 |
| **Res. CRC 8171 de 2026** (según prensa, vigente para servicios móviles desde el 1 de octubre de 2026) | Canal específico de cancelación, sin ofertas de retención; envío del CUN; ofertas solo después de terminada la interacción. *Verificar el texto oficial.* | L7 |
| **Ley 1328 de 2009** (consumidor financiero) | Información clara, veraz y oportuna; Sistema de Atención al Consumidor Financiero (SAC); Defensor del Consumidor Financiero. | P4, L4 |
| **Proyectos de ley de IA** (p. ej. PL 025 de 2026 Cámara) | Propuesta: los chatbots deben informar que el usuario interactúa con una IA. *En trámite.* | B1 |

Fuentes: [Ley 2300 (Función Pública)](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=213990), [Concepto Superfinanciera 93237 de 2023](https://normograma.com/keralty/compilacion/docs/concepto_superfinanciera_0093237_2023.htm),
[Ley 1328 (Función Pública)](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=36841), [CRC: línea de atención](https://www.crcom.gov.co/es/preguntas-frecuentes/linea-atencion-telefonica-mi-operador-debe-atender-las-24-horas),
[Bloomberg Línea: cancelación sin trabas](https://www.bloomberglinea.com/latinoamerica/colombia/quiere-cancelar-su-plan-de-celular-en-colombia-desde-hoy-el-operador-debe-ofrecerle-un-canal-digital-sin-trabas/),
[Telesemana: CRC y retención](https://www.telesemana.com/blog/2026/10/01/la-crc-obliga-a-los-operadores-telco-a-tramitar-pedidos-de-cancelacion-de-servicios-sin-interponer-estrategias-de-retencion/),
[Proyecto de ley 025 de 2026](https://www.camara.gov.co/wp-content/uploads/2026/07/proyectos-ley/documentos/proyecto-36127/P.L.025-2026SC-INTELIGENCIA-ARTIFICIAL.pdf).

## 3. Buenas prácticas de calidad (QA) adoptadas

| Práctica | Cómo la aplica Alómetro |
|---|---|
| **Errores críticos separados de la nota** (modelo COPC: errores que afectan al cliente final, al negocio y al cumplimiento) | Tres categorías: cliente, negocio, cumplimiento; se reporta el % de interacciones *libres* de error crítico. |
| **Calibración** cuantitativa y por atributo (COPC exige calibrar al personal de monitoreo; la concordancia debe medirse por criterio, no solo por nota final) | `alometro calibrar`: kappa de Cohen por criterio frente a analistas humanos. |
| **Contención con resolución y recontacto** (la contención sola se puede inflar con un bot que no escala) | I06 «Contención falsa» y comparación contención aparente vs. real. |
| **Traspaso con contexto** (intención, datos verificados, lo ya intentado) | B4 y E2. |
| **Escalamiento por frustración o peticiones repetidas** | B2/B2C + trayectoria emocional. |
| **ISO 18295-1:2017** (requisitos para centros de contacto: medición de experiencia, quejas, aseguramiento de calidad) | Estructura de indicadores de resultado y de quejas (R2). |
| **Esfuerzo del cliente** (CES) | Índice de esfuerzo 0-10 e I13. |

Fuentes: [ICMI: calibración](https://icmi.com/resources/2020/calibrate-your-contact-center-quality-management-program), [Call Centre Helper](https://callcentrehelper.com/how-to-calibrate-quality-scores-110947.htm),
[NICE: señales de que el chatbot hace daño](https://www.nice.com/answers/signs-your-ai-chatbot-is-doing-more-harm-than-good), [BSI: ISO 18295-1](https://knowledge.bsigroup.com/products/customer-contact-centres-requirements-for-customer-contact-centres).
*Las cifras de proveedores sobre contención (20-90 %) no están auditadas y no se usan como metas.*

## 4. El mercado

* Sector BPO colombiano: ≈ 750.000-790.000 empleos formales y exportaciones de servicios BPO/KPO de ≈ USD 2.934 millones en 2025, con EE. UU. como destino del ≈ 60 % (las cifras varían según la fuente).
  [Valora Analitik](https://www.valoraanalitik.com/la-industria-bpo-genera-mas-de-700-000-empleos-en-colombia/), [Noticias RCN](https://www.noticiasrcn.com/economia/call-center-bpo-tiene-mas-de-750-mil-empleos-en-colombia-891279), [La Nota Económica](https://lanotaeconomica.com.co/movidas-empresarial/bpo-colombiano-entra-a-2026-como-motor-de-empleo-y-exportaciones-pero-enfrenta-el-reto-de-sostener-la-confianza-global/)
* Concentración: Bogotá (≈ 47 % del empleo del sector en un estudio de 2022) y Medellín, seguidos de Barranquilla y Cali.

## 5. Lo que Alómetro todavía no cubre

* Audio: trabaja sobre transcripciones (cualquier motor de voz a texto sirve). El tono de voz y los silencios largos solo se usan si vienen en los datos.
* Las reglas léxicas no entienden ironía ni casos muy ambiguos: por eso cada hallazgo trae su evidencia para revisión humana, y por eso existe la calibración.
* Las metas por defecto no son benchmarks auditados: deben fijarse con la línea base de cada operación.
