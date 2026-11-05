"""Léxicos y patrones (español de Colombia) sobre texto NORMALIZADO.

Normalizado = minúsculas, sin tildes y ñ -> n (ver `texto.normalizar`).
Cada lista es una lista de expresiones regulares. Se mantienen aquí, separadas
de la lógica, para que un equipo de calidad pueda revisarlas y ampliarlas sin
tocar el motor.
"""

from __future__ import annotations

from .texto import compilar

# ---------------------------------------------------------------------------
# Cliente: petición de atención humana
# ---------------------------------------------------------------------------
_PERSONA = r"(asesor|asesora|asesores|humano|humana|persona|alguien|agente|operador|operadora|funcionario|funcionaria|ser humano|gente)"
PETICION_HUMANO = compilar([
    rf"\b(hablar|comunicar(me)?|pasar(me)?|contactar(me)?|atender(me)?|comuniqueme|paseme|paseme|transfier(e|a)me|conecte(me)?|comunicame|pasame)\b.{{0,30}}\b{_PERSONA}\b",
    rf"\b(quiero|necesito|exijo|deme|denme|regaleme|un|una)\s+(un\s+|una\s+|con\s+un\s+|con\s+una\s+)?{_PERSONA}\b(?!\s+(me\s+)?(dijo|llamo|escribio|ofrecio|vino))",
    r"\b(persona|humano) (real|de verdad|de carne y hueso)\b",
    r"\bno (quiero|me sirve|necesito) (hablar|chatear|escribir)?\s*(con )?(un |una |el |la )?(robot|maquina|bot|grabacion|contestadora|asistente virtual)\b",
    r"\b(robot|maquina|bot) no\b.{0,20}\b(entiende|sirve|ayuda)\b",
    r"^\s*(asesor|asesora|agente|humano|operador|persona)\s*[.!?]*\s*(por favor|porfa|ya)?\s*[.!?]*$",
])

# ---------------------------------------------------------------------------
# Bot: respuestas de "no entendí" (fallback)
# ---------------------------------------------------------------------------
FALLBACK_BOT = compilar([
    r"\bno (te |le )?(entendi|comprendi|logre entender|logro entender|pude entender|comprendo|entiendo)\b",
    r"\b(puedes|podrias|puede|podria) (reformular|repetir|escribirlo de otra forma|decirlo de otra manera)\b",
    r"\b(opcion|respuesta) (no valida|invalida|incorrecta)\b",
    r"\b(selecciona|elige|escoge|seleccione|elija|marque|digite) (una|alguna) de las opciones\b",
    r"\bintenta(lo)? (de nuevo|nuevamente|otra vez)\b",
    r"\bno tengo informacion sobre (eso|esa consulta|lo que)\b",
    r"\blo siento,? (aun )?no (se|puedo ayudarte con) (eso|esa)\b",
])

# ---------------------------------------------------------------------------
# Bot: transparencia y salida a humano
# ---------------------------------------------------------------------------
BOT_SE_IDENTIFICA = compilar([
    r"\b(asistente|agente|asesor|asesora) (virtual|digital|automatico|automatizado)\b",
    r"\bsoy (un |una )?(bot|chatbot|robot|asistente (virtual|digital))\b",
    r"\binteligencia artificial\b",
    r"\b(respuestas?|atencion) automatica\b",
])
BOT_OFRECE_HUMANO = compilar([
    rf"\b(comunicar|transferir|pasar|conectar|comunico|transfiero|paso|conecto)\b.{{0,40}}\b{_PERSONA}\b",
    rf"\b(escribe|marca|digita|presiona|oprime|escriba|marque|digite)\b.{{0,15}}\b(para|y)?\s*(hablar|comunicarte|comunicarse|chatear)\b.{{0,15}}\b{_PERSONA}\b",
    rf"\b(un|una|nuestro|nuestra|nuestros) {_PERSONA} (te|le) (atendera|contactara|ayudara|escribira|respondera)\b",
])

# ---------------------------------------------------------------------------
# Frustración del cliente (peso por coincidencia)
# ---------------------------------------------------------------------------
FRUSTRACION_FUERTE = compilar([  # 3 puntos
    r"\bpesim[oa]s?\b", r"\bes el colmo\b", r"\bfalta de respeto\b", r"\buna burla\b",
    r"\b(me|nos) (estan|quieren) robando\b", r"\bladrones\b", r"\bestafa(dores)?\b",
    r"\bno (sirven?|sirve) (para )?nada\b", r"\bporqueria\b", r"\bhart[oa]s?\b",
    r"\bcansad[oa]s? (de|con)\b", r"\bindignante\b", r"\bindignad[oa]\b", r"\bvergonzoso\b",
    r"\bque verguenza\b", r"\binaceptable\b", r"\bmamad[oa]\b", r"\babsurdo\b",
    r"\bun desastre\b", r"\bterrible\b", r"\bhorrible\b", r"\bme tienen (aburrid|mamad|cansad)",
    r"\bno (lo |la )?(puedo|puede) creer\b", r"\bdescarad[oa]s?\b", r"\bsinverguenza",
])
FRUSTRACION_MEDIA = compilar([  # 2 puntos
    r"\botra vez\b", r"\bde nuevo\b", r"\bnuevamente\b",
    r"\bya (le|les|te|lo|se lo|se los) (dije|explique|conte|habia dicho|informe)\b",
    r"\bcomo (ya )?(le|les|te) dije\b",
    r"\b(tercera|cuarta|quinta|sexta|enesima) vez\b", r"\bvarias veces\b", r"\bmil veces\b",
    r"\bllevo (mas de )?(\d+|un|una|dos|tres|cuatro|cinco|seis|varios|varias) (dias|dia|semanas|semana|meses|mes|horas|hora|anos)\b",
    r"\bnadie (me )?(soluciona|ayuda|responde|da razon|resuelve|contesta)\b",
    r"\bsigue igual\b", r"\bsigo (igual|sin)\b", r"\bsigue sin\b", r"\btodavia no\b", r"\baun no\b",
    r"\bno me (han|ha) (solucionado|resuelto|devuelto|respondido|llamado|arreglado)\b",
    r"\bno (me )?(entiende|entienden|esta entendiendo|escucha|escuchan)\b",
    r"\bno puede ser\b", r"\bque pereza\b", r"\bno es justo\b", r"\bperdi(endo)? (el|mi) tiempo\b",
    r"\bpara nada\b", r"\bno me (sirvio|sirve|ayudo)\b",
])
FRUSTRACION_LEVE = compilar([  # 1 punto
    r"\bmolest[oa]s?\b", r"\binconforme\b", r"\bpreocupad[oa]\b", r"\burgente\b",
    r"\bayudeme por favor\b", r"\bnada que\b", r"\bdemasiado\b", r"\bdemorad[oa]\b",
    r"\bespere y espere\b", r"\bmucho tiempo\b", r"\bdisgustad[oa]\b",
])
FRUSTRACION_EMOJI = compilar([r"[\U0001F621\U0001F92C\U0001F620\U0001F47F\U0001F4A2\U0001F44E\U0001F624\U0001F612\U0001F644\U0001F62B\U0001F629]"])  # 😡🤬😠👿💢👎😤😒🙄😫😩
POSITIVO_CLIENTE = compilar([  # resta 2 puntos
    r"\b(muchas |mil |muy amable,? )?gracias\b", r"\bmuy amable\b", r"\bperfecto\b", r"\bexcelente\b",
    r"\bque bien\b", r"\bsuper\b", r"\bme sirvio\b", r"\bgenial\b", r"\bbuenisimo\b",
    r"\bdios (le|te) pague\b", r"\bque amable\b",
])
ACUSE_CLIENTE = compilar([r"^\s*(ok|okey|okay|vale|entendido|de acuerdo|listo|bueno|perfecto|entiendo)\s*[.!]*\s*$"])
AMENAZA_EXTERNA = compilar([
    r"\bsuperintendencia\b", r"\bsuper(industria|financiera|salud|servicios)\b", r"\bsic\b",
    r"\btutela\b", r"\bdemandar(los|las|la|lo)?\b", r"\blos demando\b", r"\buna demanda (contra|a)\b",
    r"\b(voy a|vamos a|los voy a)\b.{0,30}\b(abogad[oa]|demanda|tutela)\b", r"\bmi abogad[oa] (los|lo|las|va a|les)\b",
    r"\b(quejar|queja|denunciar|demandar|reportar)\w*\b.{0,15}\b(ante|en|a) (la )?(super|superintendencia|sic|superfinanciera|supersalud|defensoria)\b",
    r"\bderecho de peticion\b",
    r"\bdenuncia(r|re|rlos|mos)?\b", r"\blos denuncio\b",
    r"\b(voy a|los voy a|lo voy a|la voy a)\s+(publicar|subir|quemar|exponer|denunciar|poner|escrachar)\b.{0,30}\b(redes|twitter|instagram|tiktok|facebook)\b",
    r"\b(publicar|subir|contar|poner)(lo|la)? en (redes sociales|las redes|twitter|instagram|tiktok|facebook)\b",
    r"\bdefensor(ia)? del consumidor\b", r"\bvoy a (publicar|poner una queja formal)\b",
    r"\bcrc\b",
])
INSULTOS = compilar([
    r"\bidiotas?\b", r"\bestupid[oa]s?\b", r"\bimbeciles?\b", r"\binutil(es)?\b",
    r"\bmalparid[oa]s?\b", r"\bhijueputas?\b", r"\bhp\b", r"\bhpta\b", r"\bgonorreas?\b",
    r"\bcarechimbas?\b", r"\bpendej[oa]s?\b", r"\bbrut[oa]s?\b", r"\bincompetentes?\b",
    r"\bineptos?\b", r"\bineptas?\b", r"\bguevon(es)?\b", r"\bhuevon(es)?\b", r"\bmamertos?\b",
    r"\bimbecil\b", r"\bladr[oó]n(es)?\b",
])

# ---------------------------------------------------------------------------
# Resolución
# ---------------------------------------------------------------------------
_ACCION = r"(aplico|aplicad[oa]|realizo|realizad[oa]|activo|activad[oa]|reverso|reversad[oa]|ajusto|ajustad[oa]|devolvio|reintegro|restablecio|restablecid[oa]|habilito|habilitad[oa]|desbloqueo|desbloquead[oa]|cambio|genero|generad[oa]|programo|programad[oa]|actualizo|actualizad[oa]|corrigio|corregid[oa]|solucionad[oa]|resuelt[oa]|registrad[oa]|cancelad[oa]|anulad[oa]|enviad[oa]|abonad[oa]|radicad[oa]|bloquead[oa])"
_ACCION_FINAL = _ACCION.replace("|registrad[oa]", "").replace("|radicad[oa]", "")
RESUELTO_EMPRESA = compilar([
    rf"\bya (quedo|queda|esta|se|le|te|lo|la)\b.{{0,25}}\b{_ACCION_FINAL}\b", r"\bya (lo|la) (levante|active|corregi|solucione|desbloquee|reverse|aplique)\b",
    rf"\b(quedo|queda|quedara|ha quedado) {_ACCION_FINAL}\b", r"\b(quedo|queda|quedara) (list[oa]|reflejad[oa]|activ[oa])\b",
    r"\bacabo de (aplicar|realizar|activar|reversar|ajustar|enviar|generar|desbloquear|restablecer|corregir|habilitar|abonar|programar)\b",
    r"\bya (esta|quedo) (solucionado|resuelto|activo|activa|funcionando|listo|lista|habilitado|habilitada|normalizado)\b",
    r"\b(el|la|su) (ajuste|devolucion|reverso|cambio|reintegro|abono|descuento) (ya )?(quedo|se aplico|fue aplicado|queda aplicado)\b",
    r"\bqueda(ra)? reflejado\b", r"\bproblema (quedo )?(solucionado|resuelto)\b",
    r"\bya (puede|puedes) (ingresar|usar|navegar|llamar|disfrutar)\b",
])
RESUELTO_CLIENTE = compilar([
    r"\bya (me )?(funciona|sirve|aparece|llego|quedo|entro|carga|conecta|abre)\b",
    r"\b(quedo|esta) (solucionado|resuelto|listo)\b", r"\bya me (solucionaron|resolvieron|ayudaron|llego)\b",
    r"\b(perfecto|listo|excelente|super|genial|muy bien),? (muchas |mil )?gracias\b",
    r"\bme (sirvio|ayudo) (mucho|bastante)?\b", r"\bproblema resuelto\b", r"\bya funciona\b",
])
NO_RESUELTO_EMPRESA = compilar([
    r"\bno (le |te |les )?(puedo|podemos|es posible) (ayudar|hacer nada|solucionar|resolver|colaborar)\b",
    r"\bno tenemos (sistema|acceso|como)\b", r"\b(el )?sistema (esta |se )?(caido|lento|cayo|no me deja|no me permite|no carga)\b",
    r"\b(llame|llamenos|vuelva a llamar|comuniquese|escriba|intente|intentelo|vuelva a escribir)\b.{0,15}\b(mas tarde|en otro momento|nuevamente|despues|manana|luego)\b",
    r"\beso no (depende|es) (de nosotros|conmigo|de mi area|de esta area)\b", r"\bno es (de )?(mi|nuestra) (area|competencia)\b",
    r"\beso lo (maneja|ve|tramita) otra area\b", r"\bno tengo (esa )?informacion\b", r"\bno tengo como (verlo|validarlo|saberlo)\b",
    r"\b(debe|tiene que|tendria que) (acercarse|ir|dirigirse) a (una |la )?(oficina|sede|sucursal|punto)\b",
    r"\bno (hay|tenemos) (nada|ninguna) (que hacer|solucion|forma)\b",
    r"\bno (le |te )?(se|sabria|sabemos|puedo) (decir|informar|dar razon|confirmar)\b",
    r"\b(ese|este|eso|ese tipo de) (tema|caso|asunto|tramite)?\s*no (lo )?(manejo|manejamos|vemos|tramitamos|es de aqui)\b",
    r"\bno (lo|la) (tengo|tenemos|manejo|manejamos)\b", r"\bno (le |te )?(puedo|podemos) dar (esa )?(informacion|razon)\b",
    r"\b(tiene|tienes|toca|hay) que esperar\b(?!.{0,30}\b(dias|horas|semanas)\b)", r"\beso se demora\b",
])
NO_RESUELTO_CLIENTE = compilar([
    r"\b(o sea|entonces|osea) (que )?no (me )?(van a |pueden |lo van a )?(solucionan|solucionaron|ayudan|resuelven|solucionar|ayudar|resolver)\b",
    r"\bsigue igual\b", r"\bsigo (igual|sin)\b", r"\bno me (solucionaron|resolvieron|ayudaron|sirvio|sirve)\b",
    r"\bno sirvio (de )?nada\b", r"\bperdi (el|mi) tiempo\b", r"\bno me (dieron|dan) (solucion|respuesta)\b",
    r"\bentonces para que\b", r"\bno resolvieron nada\b", r"\bme toca (llamar|escribir|ir) (otra vez|de nuevo|nuevamente)\b",
    r"\bno funciono\b", r"\btodavia no (me )?(funciona|sirve|llega)\b",
    r"\bsigue(n)? (igual|lent|sin|mal|fallando|caid|cobrando|apareciendo|saliendo)\w*", r"\bno ha (servido|funcionado|llegado)\b",
    r"\btodavia (sigue|no)\b", r"\bno (sirve|sirven) (para )?nada\b", r"\besto no sirve\b", r"\bmejor me (cambio|voy) (de|a otra)\b",
])

# ---------------------------------------------------------------------------
# Quejas, radicados y plazos
# ---------------------------------------------------------------------------
QUEJA_CLIENTE = compilar([
    r"\bqueja\b", r"\breclamo\b", r"\breclamar\b", r"\bpqrs?\b", r"\bderecho de peticion\b",
    r"\bcobr(o|aron|an)\b.{0,30}\b(no reconozco|que no|indebid|de mas|doble|sin autoriz|sin que)\b",
    r"\b(no reconozco|no autorice|no he autorizado)\b", r"\breembolso\b", r"\bdevolucion de (mi |la )?(plata|dinero)\b",
    r"\binconformidad\b", r"\bme cobraron\b",
])
RADICADO = compilar([
    r"\bnumero de (pqrs?|peticion|queja|reclamo|reclamacion|radicado|caso|ticket|solicitud|seguimiento|tramite|incidente|requerimiento|servicio)\b\D{0,20}[a-z0-9-]*\d{4,}",
    r"\b(solicitud|reclamo|reclamacion|queja|peticion|pqrs?|caso|requerimiento|incidencia)\b.{0,25}\b(numero|no\.?|#|n°)\s*[a-z0-9-]*\d{4,}",
    r"\b(radicado|radicacion|cun|codigo unico|numero de (caso|solicitud|radicado|ticket|seguimiento|reclamo|queja|tramite|incidente)|ticket|caso)\b\D{0,30}?[a-z0-9-]*\d{4,}[a-z0-9-]*",
])
PLAZO = compilar([
    r"\b(\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|diez|doce|quince|veinte|treinta|cuarenta y ocho|setenta y dos|veinticuatro) (dias|horas) (habiles|calendario)\b",
    r"\b(en|dentro de|maximo|a mas tardar en|plazo de)\b.{0,12}\b(\d+|un|una|dos|tres|cinco|diez|quince|veinticuatro|cuarenta y ocho|setenta y dos) (dias|horas|semanas)\b",
    r"\ba mas tardar (el|este|el proximo)\b", r"\bantes del (\d+|lunes|martes|miercoles|jueves|viernes|sabado)\b",
    r"\bplazo (de respuesta|maximo|legal)\b",
    r"\b(manana|pasado manana|el (lunes|martes|miercoles|jueves|viernes|sabado))\b.{0,25}\b(a las|entre las|en la (manana|tarde)|antes de las)\b",
    r"\b(queda|quedo|quedara) (programad|agendad)[oa]s? para\b",
    r"\bal cierre del (ciclo|periodo) de facturacion\b", r"\bhoy (a las|antes de las|en la (tarde|noche|manana))\b",
])

# ---------------------------------------------------------------------------
# Esfuerzo del cliente
# ---------------------------------------------------------------------------
TRANSFERENCIA = compilar([
    r"\b(le|lo|la|te) (voy a |vamos a )?(transfiero|transferir|comunico|comunicar|paso|pasar|remito|remitir|traslado|trasladar)\b.{0,40}\b(area|departamento|asesor|asesora|companer[oa]|especialista|linea|extension|dependencia|supervisor|supervisora|encargad[oa]|grupo|equipo)\b",
    r"\btransfiriendo\b", r"\b(llamada|conversacion|chat) (transferid[oa]|en transferencia)\b",
    r"\btransferencia (a|al|en curso)\b",
])
ESPERA = compilar([
    r"\b(me regala|me permite|permitame|permiteme|deme|regaleme|dame|me da|me concede|regalame)\b.{0,10}\b(un |una )?(momento|momentico|minuto|minutico|segundo|segundito|instante)\b",
    r"\b(en|lo dejo en|la dejo en|lo pongo en|la pongo en) espera\b", r"\bno cuelgue\b", r"\bpor favor espere\b",
])
REDIRECCION = compilar([
    r"\b(debe|tiene que|toca|debera|tendria que)\b.{0,25}\b(por|en|a traves de|desde|mediante)\s+(la |el |nuestra |nuestro |una )?(pagina|web|app|aplicacion|correo|portal|oficina|sucursal|sede|linea|formulario)\b",
    r"\b(comuniquese|contacte|llame|escriba|dirijase|acuda)\b.{0,10}\b(con|a)\s+(la|el)\s+(transportadora|proveedor|fabricante|banco|eps|aseguradora|entidad|operador|tienda|almacen)\b",
    r"\b(tiene que|tienes que|debe|debes|debera|toca|tendria que)\s+(acercarse|acercarte|ir|dirigirse|dirigirte|acudir|llamar|escribir|ingresar|entrar)\b.{0,30}\b(oficina|sede|sucursal|punto|pagina|web|app|aplicacion|correo|linea|portal|whatsapp)\b",
    r"\b(ingrese|ingresa|entre|entra|descargue|descarga|escriba|escribe|envie|envia|mande|acerquese|dirijase|debe ir|tiene que ir|consulte|consulta|llame|llama)\b.{0,35}\b(pagina|web|app|aplicacion|correo|oficina|punto de atencion|sucursal|portal|whatsapp|linea|sede|formulario|pagina web)\b",
])

# Solicitudes de datos (para detectar pérdida de contexto)
_PIDE = r"(regala|regalame|confirma|confirmame|confirmeme|indica|indicame|indiqueme|da|dame|deme|brinda|brindame|puede dar|podria dar|dicta|dicteme|digita|digite|ingrese|ingresa|escriba|escribe|suministra|suministre|proporcione|cual es|me repite|repitame|necesito)"
DATOS = {
    "documento": rf"\b{_PIDE}\b.{{0,30}}\b(cedula|documento|numero de identificacion|identificacion|nit|c\.?c\.?)\b",
    "telefono": rf"\b{_PIDE}\b.{{0,30}}\b(numero de (celular|telefono|linea|contacto)|celular|telefono|linea)\b",
    "correo": rf"\b{_PIDE}\b.{{0,30}}\b(correo|email|e-mail|correo electronico)\b",
    "nombre": rf"\b{_PIDE}\b.{{0,30}}\b(nombre completo|su nombre|tu nombre|nombre del titular)\b",
    "cuenta": rf"\b{_PIDE}\b.{{0,30}}\b(numero de (cuenta|contrato|cliente|factura|pedido|orden|poliza|credito|tarjeta|referencia))\b",
    "direccion": rf"\b{_PIDE}\b.{{0,30}}\b(direccion|direccion de (instalacion|residencia|entrega))\b",
}
_SIN_VERBO = {
    "documento": r"(cedula|documento|numero de documento|numero de identificacion|identificacion)",
    "telefono": r"(numero de (celular|telefono|contacto)|celular)",
    "correo": r"(correo|correo electronico|email)",
    "nombre": r"(nombre completo)",
    "cuenta": r"(numero de (cuenta|contrato|cliente|factura|pedido|orden|poliza|credito|referencia)|poliza|contrato)",
    "direccion": r"(direccion)",
}
DATOS = {k: compilar([v, rf"\b(su|tu|el|la)\s+(numero de\s+)?{_SIN_VERBO[k]}\b[^.?]{{0,20}}(por favor|porfa|\?)"]) for k, v in DATOS.items()}
CONTEXTO_RECONOCIDO = compilar([
    r"\b(veo|ya veo|observo|reviso) (que|en el historial|en el sistema|la conversacion|lo que)\b",
    r"\b(segun|de acuerdo con) (lo que|la conversacion|el historial|lo que (le )?(escribio|conto|indico))\b",
    r"\bya (tengo|cuento con) (su|tu|la) (informacion|datos|caso|consulta|historial)\b",
    r"\b(el|la) (asistente|bot|asistente virtual) me (paso|transfirio|compartio|dejo)\b",
    r"\bestaba (consultando|preguntando|reportando)\b",
])

# ---------------------------------------------------------------------------
# Guion / protocolo
# ---------------------------------------------------------------------------
SALUDO = compilar([
    r"\bbuen(os|as|a) (dias|tardes|noches|dia|tarde|noche)\b", r"\bhola\b", r"\bbienvenid[oa]s?\b",
    r"\bgracias por (comunicarse|comunicarte|llamar|contactar|contactarnos|escribir|escribirnos)\b",
    r"\b(un )?(cordial )?saludo\b",
])
IDENTIFICACION_AGENTE = compilar([
    r"\b(mi nombre es|le habla|te habla|habla con|le atiende|te atiende|le saluda|te saluda)\b",
    r"\bsoy [a-z]+,? (de|del|asesor|asesora|su asesor|tu asesor|agente)\b",
    r"\bsoy (el|la) (asesor|asesora|agente)\b",
])
AVISO_GRABACION = compilar([
    r"\b(llamada|conversacion|comunicacion)\b.{0,30}\b(grabad|monitoread|registrad)",
    r"\b(fines|efectos) de calidad\b", r"\bpuede ser (grabada|monitoreada)\b",
])
INDAGACION = compilar([
    r"\ben que (le |te |les )?(puedo|podemos|podria) (ayudar|colaborar|servir|asesorar)\b",
    r"\bcuenteme\b", r"\bcuentame\b", r"\bque (le |te )?(paso|sucede|ocurre|esta pasando)\b",
    r"\b(me podria|me puede|podrias|me puedes) (contar|explicar|indicar|describir)\b",
    r"\bcual es (el motivo|su consulta|tu consulta|la novedad|el inconveniente|su solicitud)\b",
    r"\bdesde cuando\b", r"\b(que|cual) (inconveniente|novedad|problema) (presenta|tiene|tienes)\b",
    r"\bcomo (le |te )?puedo ayudar\b",
    r"\bque (servicio|producto|linea|plan) (quiere|quieres|desea|deseas|necesita|necesitas)\b",
    r"\b(cuantas personas|que uso le|para que (lo|la) usa|que necesita|que es lo que mas)\b",
])
VERIFICACION = compilar([
    r"\b(por|para) (su |tu )?seguridad\b",
    r"\b(validar|verificar|confirmar|corroborar) (su |tu |la )?(identidad|datos|informacion|titularidad)\b",
    r"\bfecha de (expedicion|nacimiento)\b", r"\bpreguntas? de seguridad\b",
    r"\b(me confirma|confirmeme|me regala|me indica|regaleme)\b.{0,25}\b(cedula|documento|identificacion)\b",
    r"\bcodigo de verificacion que le (enviamos|envie|llego)\b.{0,20}\b(no lo comparta|solo usted)\b",
])
INFO_SENSIBLE_CUENTA = compilar([
    r"\b(su|tu) (saldo|deuda|consumo|cupo|obligacion|mora)\b.{0,25}\b(es|de|asciende|actual|pendiente|disponible|esta en|queda en)\b",
    r"\b(tiene|tienes|presenta|presentas) (un |una )?(saldo|deuda|mora|cupo|obligacion|valor) (pendiente|vencid|de|en mora|disponible)",
    r"\b(saldo|deuda|mora|cupo|consumo|valor a pagar|valor pendiente|movimientos?)\b.{0,40}\$\s?\d",
    r"\bvalor (pendiente|adeudado|en mora)\b", r"\b(sus|tus) (movimientos|transacciones) (son|recientes|del)\b",
])
RESUMEN = compilar([
    r"\b(le|te) confirmo\b", r"\ben resumen\b", r"\bentonces quedamos\b", r"\bqueda(mos)? (entonces|de acuerdo|asi)\b",
    r"\brecapitulando\b", r"\bpara confirmar\b", r"\bcomo acordamos\b", r"\bresumiendo\b",
    r"\b(lo que|esto es lo que) (hicimos|vamos a hacer|se hizo)\b", r"\bqueda(ra)? (radicad|programad|registrad)",
])
AYUDA_ADICIONAL = compilar([
    r"\balgo mas en (lo )?que (le |te )?(pueda|podamos) (ayudar|colaborar|servir)\b",
    r"\b(alguna|otra) (otra )?(inquietud|consulta|pregunta|solicitud)\b", r"\b(puedo|podemos) (ayudarle|ayudarte|colaborarle) en algo mas\b",
    r"\bhay algo mas\b", r"\bnecesita algo mas\b", r"\bnecesitas algo mas\b", r"\balgo mas\?",
])
DESPEDIDA = compilar([
    r"\bque (tenga|tengas|tengan) (un |una )?(buen|buena|feliz|excelente|lindo|linda|bonito|bonita|bendecido|bendecida|gran) (dia|tarde|noche|semana|fin de semana)\b",
    r"\bfeliz (dia|tarde|noche)\b", r"\bhasta (luego|pronto|la proxima)\b", r"\bfue un (gusto|placer)\b",
    r"\bgracias por (comunicarse|comunicarte|llamar|su llamada|tu llamada|contactarnos|escribirnos|preferirnos|su paciencia|tu paciencia)\b",
    r"\bque este (muy )?bien\b", r"\bchao\b", r"\badios\b",
])

# ---------------------------------------------------------------------------
# Trato humano / empatía
# ---------------------------------------------------------------------------
VALIDACION = compilar([
    r"\bentiendo (perfectamente )?(su|tu|la|el) (molestia|frustracion|preocupacion|situacion|inconformidad|malestar|enojo|incomodidad|urgencia)\b",
    r"\bcomprendo (su|tu|lo|la|que|perfectamente)\b", r"\btiene(s)? (toda la )?razon\b",
    r"\blamento (mucho )?(lo|la|que|esta|esto|su|tu|el)\b", r"\bque pena (con usted|contigo|la demora|esto)\b",
    r"\bsiento mucho\b", r"\bes entendible\b", r"\b(con|tiene) toda (la )?razon\b",
    r"\b(le|te) pido (una )?(sinceras? )?disculpas por\b", r"\bme imagino (lo|que|como)\b",
    r"\bentiendo (que|como) (se siente|esto|eso|debe)\b", r"\bes muy (valido|comprensible)\b",
])
PARAFRASEO = compilar([
    r"\bsi (le |te )?entiendo bien\b", r"\blo que me (dice|cuenta|indica|comenta) es\b",
    r"\bentonces (usted|tu) (me dice|necesita|quiere|requiere|tiene)\b", r"\bpara asegurarme de (entender|haber entendido)\b",
    r"\bdejeme ver si entendi\b", r"\bme (esta|estas) diciendo que\b",
    r"\bentiendo que (usted |tu )?(necesita|quiere|tiene|le|te|requiere|desea|presenta)\b",
    r"\bsi comprendo bien\b", r"\bo sea que (usted|tu)\b", r"\b(su|tu) (caso|solicitud) es que\b",
])
APROPIACION = compilar([
    r"\b(yo )?me encargo\b", r"\bvoy a (revisar|validar|gestionar|hacer|solucionar|escalar|aplicar|radicar|tramitar|verificar|ayudarle|ayudarte|dejar)\b",
    r"\bdejeme (revisar|validar|verificar|mirar|consultar)\b", r"\bdejame (revisar|validar|verificar|mirar)\b",
    r"\blo (vamos|voy) a (solucionar|resolver|revisar)\b", r"\bcon gusto (le |te )?(ayudo|colaboro|reviso)\b",
    r"\bya mismo (lo|le|te|la)\b", r"\bme comprometo\b", r"\b(le|te) ayudo\b",
    r"\b(le|te) (puedo|podemos) ofrecer\b", r"\bprocedo (a|con)\b", r"\bmi compromiso\b",
    r"\b(le|te) (radico|activo|programo|agendo|bloqueo|registro|escalo|envio|gestiono)\b",
])
CULPA_EVASION = compilar([
    r"\busted (debio|debia|tenia que|no leyo|se equivoco|no hizo|tiene la culpa)\b",
    r"\b(es|fue) (su|tu) (culpa|responsabilidad|error)\b", r"\beso no es (mi|nuestro) problema\b",
    r"\bno es mi problema\b", r"\beso no es conmigo\b", r"\bcomo (ya )?le (dije|estoy diciendo|explique)\b",
    r"\bya le explique\b", r"\bno insista\b", r"\bes (la )?politica de la empresa\b", r"\bpues (eso|asi) es\b",
    r"\byo no (puedo|tengo) (hacer )?nada\b", r"\bno es mi culpa\b", r"\bal que le corresponde\b",
])
NEGATIVO_SIN_ALTERNATIVA = compilar([r"\bno se puede\b", r"\bno es posible\b", r"\bimposible\b"])
ALTERNATIVA = compilar([
    r"\bpero\b", r"\blo que si\b", r"\balternativa\b", r"\b(puedo|podemos) (ofrecerle|ofrecerte|hacer|proponer)\b",
    r"\ben cambio\b", r"\bopcion\b", r"\bsin embargo\b",
])
DISCULPA_GUION = compilar([
    r"\blamentamos (los|el|cualquier) inconvenientes?\b", r"\bdisculpe(n)? (las|la) molestias?\b",
    r"\bdisculpa(s)? (las|la|por las) molestias?\b", r"\bsentimos (los|el) inconvenientes?\b",
])
IRRESPETO_AGENTE = compilar([
    r"\bcallese\b", r"\bcallate\b", r"\bno me (interesa|importa) (su|tu|lo que)\b", r"\b(usted|tu) (es|eres) (un |una )?(brut|ignorante|tont|lent)",
    r"\bque (persona|senora|senor) tan\b", r"\bno sea (bobo|boba|tonto|tonta|grosero|grosera)\b",
])

# ---------------------------------------------------------------------------
# Ventas
# ---------------------------------------------------------------------------
VENTA_CERRADA = compilar([
    r"\bbienvenid[oa] a\b.{0,40}\b(familia|plan|servicio|club)\b",
    r"\bya (quedo|queda) (activ|registrad|aprobad|confirmad)", r"\bsu (pedido|orden|plan|servicio|compra|poliza|tarjeta) (quedo|queda|ha quedado) (activ|registrad|aprobad|confirmad|programad)",
    r"\bprocedo (con|a) (la |el )?(activacion|venta|instalacion|compra|registro|afiliacion)\b",
    r"\bfelicitaciones por (su|tu) (compra|nuevo|nueva|plan)\b", r"\bnumero de (pedido|orden|venta)\b",
    r"\bqueda (agendada|programada) (la )?(instalacion|entrega)\b",
    r"\b(la )?(instalacion|entrega|activacion|visita de instalacion) (queda|quedo|quedara) (programada|agendada|confirmada)\b",
    r"\bsu (solicitud|contratacion|compra|afiliacion) (quedo|queda|ha quedado) (registrada|confirmada|aprobada|radicada)\b",
])
PRECIO = compilar([
    r"\$\s?\d", r"\b\d+[.,]?\d* ?(mil|pesos|millones)\b", r"\bvalor (mensual|total|de)\b", r"\bprecio\b",
    r"\bcuesta\b", r"\btarifa\b", r"\bcargo fijo\b", r"\bcuota (mensual|de manejo)\b",
])
CONDICIONES = compilar([
    r"\bpermanencia\b", r"\bclausula\b", r"\bcontrato (de|por) (\d+|seis|doce|un|dos)\b", r"\bterminos y condiciones\b",
    r"\bcondiciones\b", r"\bvigencia\b", r"\bprecio (promocional|de promocion)\b",
    r"\b(despues|a partir) de(l)? (\d+|tres|seis|doce|primer|segundo|tercer|cuarto|septimo) (meses|mes)\b",
    r"\bsin permanencia\b", r"\bletra (pequena|menuda)\b", r"\bincremento\b",
])
RETRACTO = compilar([
    r"\bretracto\b", r"\bretracta(rse|r|rte)\b", r"\bderecho a (arrepentirse|desistir|retractarse)\b",
    r"\b(cinco|5) dias habiles\b.{0,40}\b(cancelar|arrepent|retract|desistir|devolver)\b",
    r"\b(cancelar|arrepent|retract|desistir)\w*\b.{0,40}\b(cinco|5) dias habiles\b",
])
PREGUNTA_ACEPTACION = compilar([
    r"\b(acepta|aceptas|esta de acuerdo|estas de acuerdo|autoriza|autorizas|confirma|confirmas|desea continuar|procedemos|le activo|te activo|le confirmo|te confirmo|le dejo|te dejo)\b.{0,100}\?",
])
ACEPTACION_DEBIL = compilar([
    r"\bcomo sea\b", r"\blo que sea\b", r"\bya que\b", r"\bsi toca\b", r"\bhaga lo que (quiera|sea)\b",
    r"\bpara que (me deje|deje) de\b", r"\bno se\b", r"\bdejeme pensarlo\b", r"\bmmm+\b",
])
ACEPTACION_CLIENTE = compilar([
    r"^\s*(si|sí|claro|ok|okay|dale|listo|de una|bueno|va|hagale|hagamosle)\b",
    r"\b(si )?(acepto|autorizo|confirmo|estoy de acuerdo|de acuerdo|proceda|hagale|dale pues)\b",
])
AUTORIZACION_DATOS = compilar([
    r"\b(autoriza|autorizas|autorizacion|consentimiento)\b.{0,50}\b(tratamiento|uso|manejo)\b.{0,15}\b(de )?(sus |tus |los )?datos\b",
    r"\bpolitica de (tratamiento de datos|privacidad|proteccion de datos)\b", r"\bhabeas data\b", r"\bley 1581\b",
])
RECHAZO_CLIENTE = compilar([
    r"\bno (me )?interesa\b", r"\bno,? gracias\b", r"\bno quiero\b", r"\bno estoy interesad[oa]\b",
    r"\bno (lo |la )?necesito\b", r"\bya (le |te )?dije que no\b", r"\bno me llame(n)? mas\b", r"\bno deseo\b",
])
OFERTA = compilar([
    r"\b(le|te) (puedo|podemos|quiero|queremos|vamos a) (ofrecer|regalar|dar|dejar)\b", r"\bdescuento\b", r"\bpromocion\b",
    r"\boferta\b", r"\bbeneficio\b", r"\bplan (especial|exclusivo|mas economico|mejorado)\b", r"\bsolo por hoy\b",
    r"\bunica oportunidad\b", r"\bultima oportunidad\b", r"\bgratis\b", r"\bbono\b", r"\bme regala (un|unos) (minutos|minutico)\b.{0,20}\bexplic",
    r"\bantes de (cancelar|que cancele|irse|retirarse)\b", r"\bantes (dejeme|permitame|quiero) (contarle|ofrecerle|decirle|mostrarle|comentarle)\b",
    r"\btenemos (un|una) (plan|oferta|promocion|opcion|tarifa)\b", r"\b\d+ ?% (menos|de descuento|mas barato)\b", r"\bno se (vaya|retire)\b", r"\b(le|te) mejoro\b", r"\bpiense(lo)?\b",
])

# ---------------------------------------------------------------------------
# Cobranza y seguridad
# ---------------------------------------------------------------------------
COERCION_COBRANZA = compilar([
    r"\bcarcel\b", r"\bpolicia\b", r"\bfiscalia\b", r"\bembargo (inmediato|ya|hoy|de todo)\b", r"\b(le|te) (vamos a|van a) embargar\b",
    r"\b(vamos|van|voy) a ir a (su|tu) (casa|trabajo|oficina|empresa|domicilio)\b",
    r"\bvisita (a|en) (su|tu) (casa|domicilio|trabajo|oficina|empresa)\b",
    r"\b(pasamos|pasaremos|vamos|iremos|llegamos|van a pasar|vamos a pasar|vamos a ir)\b.{0,15}\b(por|a) (su|tu) (casa|oficina|trabajo|empresa|domicilio|negocio)\b",
    r"\b(llamar|contactar|avisar|informar|escribir)(le)? a (su|tu|sus|tus|las|los) (codeudor(es)?|fiador(es)?|familia|familiares|jefe|empresa|referencias|esposa|esposo|mama|papa|vecinos|companeros)\b",
    r"\b(su|tu) (familia|jefe|empresa|esposa|esposo|mama) se va a enterar\b", r"\b(va|vas) a perder (su|tu) (casa|trabajo)\b",
    r"\b(problemas|consecuencias) legales (graves|inmediat)\b",
    r"\b(mandar|enviar|mandarle|enviarle|mandamos|enviamos)\b.{0,10}\b(un |una )?(cobrador|cobradora|abogado|gestor|alguien|visita)\b.{0,25}\b(casa|oficina|trabajo|empresa|domicilio)\b",
    r"\b(hablamos|hable|llamamos|llame|contactamos|escribimos|le contamos|le dijimos)\b.{0,10}\b(con|a) (su|tu|sus|tus) (mama|papa|familia|familiares|esposa|esposo|jefe|jefa|hermano|hermana|hijo|hija|vecinos?|referencias?|companeros)\b",
])
PIDE_CREDENCIAL = compilar([
    r"\b(me|nos) (regala|regalas|da|das|dicta|dictas|indica|indicas|confirma|confirmas|comparte|compartes|digita|dice|dices|envia|envias)\b.{0,30}\b(clave|contrasena|pin|cvv|cvc|codigo de seguridad|token|codigo otp|otp|codigo (que|de verificacion que) (le|te) (llego|llegara|enviamos))\b",
    r"\b(digite|dicte|indique|comparta|envie|digita|dicta|indica|comparte|envia|necesito|requiero|regaleme|regalame|deme|dame|digame|dime|pasame|paseme|escriba|escribe)\b.{0,20}\b(su|tu|la|el) (clave|contrasena|pin|cvv|cvc|token|codigo de seguridad)\b",
    r"\b(numeros|digitos|codigo)\b.{0,15}\b(de atras|del reverso|de seguridad|del respaldo)\b.{0,15}\b(de )?(la|su|tu) tarjeta\b",
    r"\bcual es (su|tu) (clave|contrasena|pin|cvv)\b",
    r"\b(escribame|escriba|escribe|digame|dime|dicteme|dicte|dicta|regaleme|regalame|deme|dame|me dice|me da|me dicta|me regala|me confirma|confirmeme|digite|envieme|enviame|pasame|paseme|me pasa|leame)\b.{0,40}\bcodigo\b.{0,50}\b(llego|llega|llegar|acaba de llegar|enviamos|envie|sms|mensaje|celular|correo)\b",
    r"\b(numero completo|los 16 digitos|todos los numeros)\b.{0,20}\btarjeta\b", r"\btarjeta\b.{0,50}\bfecha de (vencimiento|expiracion)\b",
])
NEGACION_CREDENCIAL = compilar([
    r"\bnunca (le |te )?(pediremos|solicitaremos|pedimos|solicitamos|vamos a pedir)\b", r"\bno (le |te )?(pediremos|solicitaremos|vamos a pedir)\b",
    r"\bno (la |lo )?comparta(s)?\b", r"\bnunca (la |lo |se la |se lo )?(comparta|compartas|de|des|entregue|revele|digas|diga)\b", r"\bno (se la |se lo )?(de|des) a nadie\b",
])

# ---------------------------------------------------------------------------
# Temas recurrentes (multietiqueta, sobre turnos del cliente)
# ---------------------------------------------------------------------------
TEMAS = {
    "facturacion": [r"\bfactura\b", r"\bcobr(o|aron|an)\b", r"\brecibo\b", r"\bcargo\b", r"\bvalor a pagar\b", r"\bme llego (muy )?(alto|caro)\b"],
    "cobro_no_reconocido": [r"\bno reconozco\b", r"\bno autorice\b", r"\bcobr\w* (doble|indebid\w*|de mas)\b", r"\bme cobraron\b.{0,30}\b(sin|que no|algo que)\b", r"\bcompra que no hice\b"],
    "falla_tecnica": [r"\bno tengo (servicio|internet|senal|linea|luz|agua|gas)\b", r"\bsin (servicio|internet|senal|luz|agua)\b", r"\bfalla\b", r"\bno (me )?funciona\b", r"\bintermitente\b", r"\b(muy )?lento\b", r"\bse (cae|cayo|corta|va)\b", r"\bno carga\b", r"\bno conecta\b"],
    "cancelacion": [r"\bcancelar\b", r"\bretirarme\b", r"\bdar de baja\b", r"\bterminar (el )?contrato\b", r"\bdarme de baja\b", r"\bcancelacion\b"],
    "portabilidad": [r"\bportabilidad\b", r"\bpasarme (a|de) (otro )?operador\b", r"\bcambiarme de operador\b"],
    "plan_precio": [r"\bplan\b", r"\bprecio\b", r"\btarifa\b", r"\bpromocion\b", r"\bsubio\b.{0,20}\b(precio|valor|tarifa)\b", r"\bme subieron\b"],
    "entrega_envio": [r"\bpedido\b", r"\benvio\b", r"\bentrega\b", r"\bno (me )?ha llegado\b", r"\bguia\b", r"\btransportadora\b", r"\bdomicilio\b"],
    "devolucion_garantia": [r"\bgarantia\b", r"\bdevolucion\b", r"\breembolso\b", r"\bretracto\b", r"\bdevolver\b"],
    "acceso_cuenta": [r"\bclave\b", r"\bcontrasena\b", r"\busuario\b", r"\bbloquead[oa]\b", r"\bno (puedo|me deja) (ingresar|entrar)\b", r"\bla app\b"],
    "fraude_seguridad": [r"\bfraude\b", r"\bestafa\b", r"\brobo\b", r"\bme robaron\b", r"\bsuplantacion\b", r"\bno fui yo\b", r"\btransaccion(es)? que no\b", r"\bhackea"],
    "deuda_cobranza": [r"\bdeuda\b", r"\bmora\b", r"\bacuerdo de pago\b", r"\bcuota\b", r"\bsaldo pendiente\b", r"\brefinanci", r"\bdatacredito\b", r"\bcentrales de riesgo\b"],
    "instalacion_visita": [r"\binstalacion\b", r"\btecnico\b", r"\bvisita\b", r"\bagendar\b", r"\bcita\b"],
    "pqr_queja": [r"\bqueja\b", r"\breclamo\b", r"\bpqrs?\b", r"\bderecho de peticion\b", r"\bradicad"],
    "salud_autorizaciones": [r"\bautorizacion\b", r"\bcita medica\b", r"\bmedicamento\b", r"\beps\b", r"\bexamen(es)?\b", r"\borden medica\b"],
}
TEMAS = {k: compilar(v) for k, v in TEMAS.items()}
