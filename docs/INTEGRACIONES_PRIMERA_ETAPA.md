# Primera etapa de integraciones

Implementación local del 10 de octubre de 2026. Sin crear cuentas externas,
aprovisionar recursos de Azure ni contratar planes. Posteriormente se autorizó
y realizó un único envío de prueba de Resend a la dirección del titular.

## GitHub: proyectos públicos

Habilitado en esta máquina mediante `GITHUB_PROJECT_ANALYSIS_ENABLED=true` en
`.local/backend.env`. Reiniciar el backend después de cambiar la configuración.

Recorrido del candidato: **Mi perfil → Evidencias de mi experiencia → Consultar
GitHub**. Introduce la URL raíz de un repositorio público y autoriza la consulta.
Revisa las tecnologías, describe tu aporte y confirma tu participación para
guardar la evidencia. Añadir tecnologías al perfil es una opción separada.

Se guarda la revisión exacta del repositorio y un resumen del análisis. La
presencia de archivos/dependencias no verifica autoría, ejecución ni dominio
profesional. No se clona ni ejecuta código, no se accede a repositorios privados
y no se utilizan los tokens del acceso social.

Límites: 2.000 entradas, 32 manifiestos de 256 KiB, respuesta de 1 MB,
presupuesto de 50 llamadas HTTP por hora y proceso, caché de 10 minutos con
hasta 32 proyectos. Estos límites son conservadores para un MVP con un solo
proceso; GitHub puede limitar antes por compartir IP con otras aplicaciones.
Las evidencias guardadas no se sincronizan automáticamente al cambiar el repo.

Los adaptadores existentes de acceso social Google/GitHub se conservan. Para
activarlos se necesita registrar una aplicación con el proveedor y configurar
su identificador/secreto; no hace falta migrar los usuarios ni la base de datos.
Con el origen local actual, los retornos son:

- `http://127.0.0.1:5173/api/v1/auth/social/github/callback`
- `http://127.0.0.1:5173/api/v1/auth/social/google/callback`

El frontend local reenvía `/api` al backend. Usar exactamente el mismo origen
en `PUBLIC_APP_URL` y en el proveedor. El acceso social necesita sesiones
habilitadas, como en el entorno aislado actual.

## Microsoft Learn: catálogo con revisión editorial

Ruta: **Administración → Catálogo educativo → Microsoft Learn**.
El conector permanece desactivado hasta disponer de una aplicación de Microsoft
Entra con acceso a Learn. La API vigente requiere autenticación; no utiliza el
antiguo catálogo anónimo.

En `.local/backend.env`, configurar en privado:

```dotenv
LEARN_ENABLED=true
LEARN_TENANT_ID=<UUID del directorio>
LEARN_CLIENT_ID=<UUID de la aplicación>
LEARN_CLIENT_SECRET=<secreto de la aplicación>
```

El secreto se queda en el servidor. No introducirlo en el chat ni en variables
`VITE_*`. El backend solicita un token con el ámbito
`https://learn.microsoft.com/.default` mediante credenciales de aplicación y lo
conserva temporalmente en memoria. No crea recursos de Azure.

1. Consultar módulos o rutas. El producto es opcional (`power-bi`, `azure`, etc.).
2. Seleccionar recursos de una página e importar como borradores.
3. Revisar cada borrador desde **Editar**: título, descripción, tiempo y, sobre
   todo, habilidades. Las etiquetas de producto son una sugerencia inicial.
4. Activar el recurso para que se ofrezca a candidatos.

La paginación se solicita manualmente; no se descarga el catálogo completo.
Las vistas previas caducan a los diez minutos y pertenecen al administrador que
las creó. Importar otra vez el mismo identificador conserva el recurso existente
y sus cambios editoriales. No hay sincronización automática ni eliminación
automática de recursos que el proveedor retire. Antes de publicarlos, revisar
también que sus condiciones siguen vigentes.

Se conservan proveedor, identificador, idioma, versión de API y fechas de origen
y consulta. No se importan alumnos ni resultados. Este catálogo no demuestra
que una persona completó la formación y no verifica certificados.

La conexión real queda pendiente de credenciales y comprobación con la cuenta
autorizada. Se probaron respuestas simuladas basadas en el contrato oficial.

## Codewars: práctica pública y referencia declarada

Habilitado en esta máquina mediante `CODEWARS_ENABLED=true` en
`.local/backend.env`. Usa la API pública de Codewars sin claves, aplicaciones
OAuth ni servicios de pago. No requiere una cuenta de Azure ni registrar dominio.

Recorrido: **Candidato → Mi perfil → Evidencias de mi experiencia → Consultar
Codewars**.

1. Escribir el nombre de usuario y autorizar la consulta pública.
2. Revisar el rango general, el total de retos resueltos y los lenguajes con
   rango y puntos de práctica. Se ignora la lista de habilidades autodeclaradas
   de Codewars y no se importan nombre, clan ni posición de clasificación.
3. Seleccionar lenguajes, describir lo practicado y declarar la titularidad de
   la cuenta. Incorporarlos a las habilidades del perfil es opcional y aparece
   desmarcado inicialmente.
4. Guardar la referencia. Consultar y guardar otra vez esa misma cuenta actualiza
   la referencia existente sin duplicarla. Retirarla desde Evidencias conserva
   las habilidades declaradas que se hayan añadido al perfil.

La referencia queda **sin verificar**. Los datos prueban lo que la API pública
informa de esa cuenta; la plataforma no autentica su titularidad y los rangos no
constituyen una certificación profesional. No se importan soluciones, no se
ejecuta código y no se aumenta una puntuación por el número de retos. Añadir
lenguajes al perfil solo los incorpora como habilidades declaradas.

La vista previa está cifrada, pertenece al candidato y vence en diez minutos.
Solo admite guardar lenguajes de esa consulta y utiliza la URL de perfil generada
por el servidor. Actualizar requiere una nueva consulta manual; no existe una
sincronización en segundo plano. La caché pública dura diez minutos, admite 32
cuentas y devuelve copias independientes. Cada proceso limita las consultas a
50 peticiones por hora, 128 KiB por respuesta y 20 lenguajes por referencia.
Se rechazan redirecciones y nombres que puedan alterar la ruta del proveedor.

Un perfil nuevo sin rangos se muestra como tal, sin inventar habilidades. Ante
errores, límites o un nombre no encontrado se explica el estado y se conserva
la posibilidad de registrar una referencia manual.

Comprobación real: consulta de un perfil público de referencia, con 13 lenguajes
devueltos. Se comprobó también la vista previa desde la API local y su estado en
administración. Ese perfil público no se guardó como evidencia de un candidato.
Evidencia: `.local/verification/codewars-public-smoke.json` e
`.local/verification/integrations-api.json` (archivos locales no versionados).
Las 30 pruebas específicas cubren consentimiento, permisos, titularidad de la
vista previa, caducidad, selección de lenguajes, actualización, retirada,
configuración desactivada, límites de red y errores del proveedor.
Regresión completa tras añadir Codewars: **556 pruebas backend aprobadas y una
omitida para PostgreSQL staging; 28 pruebas frontend aprobadas**, lint y build
correctos. La comprobación funcional se realizó mediante la API local; la
revisión visual del nuevo componente en navegador sigue pendiente por la
restricción de acceso ya indicada.

## Resend: transporte preparado y prueba real aceptada

Implementado como alternativa a SMTP sobre la bandeja de salida existente:
reservas por trabajador, reintentos limitados, caducidad de enlaces y limpieza
del cuerpo después de enviar. Los errores no exponen la respuesta del proveedor
ni las credenciales. Cada mensaje utiliza una clave de idempotencia estable.

El usuario todavía no tiene dominio propio. `scripts/local.py` sigue forzando
**correo local**, sin usar claves externas heredadas. No se envían los mensajes
de las cuentas ficticias a Internet.

Se configuró una prueba independiente con la clave privada en `.local/resend.env`,
ignorado por Git, y un único destinatario autorizado: el correo de la cuenta de
Resend. El remitente de pruebas es `onboarding@resend.dev`. Resend confirmó la
aceptación del envío real; eso no confirma entrega a la bandeja del destinatario.

Comando desde la raíz del proyecto:

```powershell
& backend/.venv/Scripts/python.exe -X utf8 scripts/resend_test.py
```

El comando no lee la base de datos ni procesa la bandeja de salida. No acepta
destinatarios ni contenido por argumentos. Lee únicamente `.local/resend.env`:

```dotenv
RESEND_TEST_ENABLED=true
RESEND_API_KEY=<clave privada>
RESEND_FROM=onboarding@resend.dev
RESEND_TEST_RECIPIENT=<correo de la cuenta Resend>
```

El estado privado está en `.local/verification/resend-test.json`. Si ya fue
aceptado, repetir el comando no genera otro correo. Ante un fallo o respuesta
incierta, los intentos manuales conservan la clave de idempotencia; después de
23 horas se exige revisar el panel antes de repetir. Un bloqueo impide ejecutar
dos comandos simultáneamente. No borrar el estado para forzar reenvíos.

Para enviar a personas distintas del titular se necesita un dominio propio
verificado. La prueba no habilita automáticamente el correo de la aplicación.

Para una activación futura fuera del lanzador aislado se necesitarán una cuenta
de Resend, dominio/remitente verificado y una prueba a un destinatario autorizado:

```dotenv
LOCAL_MAIL_ENABLED=false
SMTP_ENABLED=false
RESEND_ENABLED=true
RESEND_API_KEY=<clave privada>
RESEND_FROM=acceso@dominio-verificado.com
```

Solo puede activarse un transporte. La configuración no prueba entrega efectiva.
Resend aplica sus propias cuotas y condiciones; el conector no impone un límite
de gasto en la cuenta del proveedor. Mantener el plan gratuito y sus límites al
activarlo. La idempotencia del proveedor dura 24 horas; una recuperación manual
fuera de ese plazo requiere revisar el estado antes de reenviar.

### Diseño de los mensajes y dominio propuesto

Resend y SMTP comparten una plantilla HTML con cabecera TalentSync, acento cian,
tipografía legible, contenido de hasta 600 px y adaptación móvil. Se conserva el
texto original como alternativa para clientes que no muestran HTML. No carga
imágenes externas, fuentes, scripts ni píxeles de seguimiento.

Los enlaces de confirmación, recuperación e invitación tienen botón y enlace
alternativo. Solo se convierten en botones las rutas conocidas del origen
configurado en `PUBLIC_APP_URL`. El contenido y los atributos se escapan. El
preencabezado no incluye enlaces ni tokens del cuerpo. Resend muestra el nombre
del remitente como **TalentSync**, manteniendo su dirección configurada.

Crear vistas previas sin leer claves ni enviar mensajes:

```powershell
& backend/.venv/Scripts/python.exe -X utf8 scripts/resend_test.py --preview
```

Archivos: `.local/verification/email-preview.html` y
`.local/verification/email-confirmation-preview.html`. El segundo usa un enlace
de demostración `example.invalid`, sin tokens reales. El mensaje aceptado antes
de este cambio no se reenvió ni se eliminó su estado de idempotencia. La
apariencia en cada cliente de correo deberá comprobarse con un nuevo envío
autorizado; las pruebas automáticas validan la estructura y el transporte.

Actualmente el dominio de prueba es **resend.dev**. Propuesta para una futura
compra: **talentsyncempleo.com**, con el subdominio **correo.talentsyncempleo.com**
y remitente **TalentSync <notificaciones@correo.talentsyncempleo.com>**. Es una
propuesta pendiente de comprobar disponibilidad y registro, no un dominio
comprado ni configurado. No se cambió la dirección del remitente real. Después
de adquirir el dominio, verificar el subdominio en Resend con los registros DNS
que muestre su panel; no inventar valores DKIM/SPF ni modificar registros MX de
una bandeja existente sin revisar el propósito.

Validación adicional actualizada: 65 pruebas de correo e integraciones aprobadas,
incluidas nueve para la prueba aislada y cinco para la plantilla. Cubren
destinatario único, configuración inválida, reintentos, caducidad, concurrencia,
prevención de duplicados, vistas previas sin envío, escape de HTML, enlaces del
origen autorizado y versiones HTML/texto.

## Validación y siguientes conexiones

Pruebas automáticas: permisos de rol, consentimiento, aislamiento de vistas
previas, selección de señales, deduplicación, conservación de ediciones,
límites de respuesta, redirecciones, errores sanitizados, configuración de
correo e idempotencia. Las pruebas aíslan credenciales y usan transportes
simulados; no envían correo ni dependen de los proveedores.

Resultado: 512 pruebas backend aprobadas y una omitida para PostgreSQL staging;
28 pruebas frontend aprobadas, lint Python/JavaScript y build de producción
correctos. La API local se comprobó con cuentas ficticias: vista previa real de
GitHub, Microsoft Learn pendiente de credenciales, correo exclusivamente local
y revisión sin segundo factor. Evidencia sin secretos en
`.local/verification/integrations-api.json`.

La revisión visual del navegador quedó pendiente porque su política de acceso
bloqueó la pestaña local; no se considera validada la apariencia interactiva.

Quedan para otras etapas: YouTube curado, oferta oficial SENA/Sapiencia,
registros empresariales autorizados, fuentes salariales
con cobertura comprobada, calendarios y validación de certificados por emisor.
No se debe inferir fraude por ausencia de logo o de un registro en una fuente
incompleta, ni acreditar competencias a partir de un contador de commits.

Referencias oficiales:

- [Autenticación y paginación de Learn](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-get-started)
- [Contrato del catálogo de Learn](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-catalog-endpoints-developer-reference)
- [Preguntas frecuentes y coste de Learn](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-faq)
- [Envío de correo con Resend](https://resend.com/docs/api-reference/emails/send-email)
- [Idempotencia de Resend](https://resend.com/docs/dashboard/emails/idempotency-keys)
- [Restricción del remitente de pruebas](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain)
- [Límites de GitHub REST](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [API pública de Codewars](https://dev.codewars.com/)

## Ampliación editorial de educación · 2026-10-10

`backend/app/data/education_catalog.json` contiene 34 recursos de 11 proveedores
(24 gratuitos y 10 de pago), con identificadores estables, lista de dominios
permitidos, fecha de revisión y metadatos de contenido/acceso/certificación.
Es una selección editorial de páginas oficiales, no una sincronización automática
ni una integración de matrícula o emisión de certificados. Complementa el
conector autenticado de Microsoft Learn, que continúa requiriendo acceso Entra.

Fuentes incluidas: Microsoft Learn (5), Google Career Certificates / AI Essentials
(7), Google Skillshop (2), HubSpot Academy (5), IBM en Coursera (2), Cisco (3),
freeCodeCamp (2), OpenLearn (4), AWS Skill Builder (1), Harvard CS50 (2), Rutgers
en Coursera (1). Los resúmenes están redactados para TalentSync; los títulos de
presentación en español no implican que todo el material esté en español.
Los idiomas declarados se muestran en la ficha y se pueden filtrar.

Rutas de administración nuevas:

- `GET /api/v1/admin/learning/sources/curated`: selección y revisión vigente.
- `POST /api/v1/admin/learning/sources/curated/import`: revisión, hasta cincuenta
  IDs distintos y `publish=false` por defecto. Solo acepta IDs del catálogo del
  servidor; no permite inyectar contenido o enlaces mediante esta operación.
- Respuestas 409 por revisión desactualizada y 422 por IDs desconocidos,
  duplicados, selección vacía o límite del catálogo. Importación atómica antes
  de escribir y límite vigente de doscientos recursos administrables.

Los IDs importados son deterministas. Repetir no publica ni sobrescribe recursos
ya existentes. Los formularios antiguos conservan los detalles enriquecidos si
no los envían; el editor actual permite actualizarlos. Las referencias estáticas
anteriores con la misma URL se retiran de la oferta nueva y siguen resolviendo
planes guardados una vez que el nuevo curso se publica. Importar un borrador no
retira la referencia anterior. Se conserva una marca interna de publicación para
que archivar posteriormente un curso no reviva su referencia antigua.

No se automatizan pagos, inscripciones, extracción de certificados ni seguimiento
de alumnos. El tiempo estimado de TalentSync se identifica en `duration_notes`.
El acceso y el certificado tienen condiciones distintas: Learn puede cobrar sus
exámenes, Google/IBM/Rutgers pueden requerir suscripción, y CS50 distingue su
certificado gratuito del certificado verificado de edX de pago. Las prácticas de
nube o las licencias adicionales pueden generar cargos fuera de TalentSync.
No se requiere activar esos servicios para consultar la biblioteca local.

Mantenimiento: revisar las páginas oficiales, actualizar el JSON y su fecha de
revisión, reiniciar el backend, ejecutar las pruebas y revisar las publicaciones existentes desde el
editor. La importación conserva deliberadamente ediciones y archivados anteriores;
una revisión del JSON no actualiza silenciosamente los cursos ya publicados.

Validación local: 570 pruebas backend aprobadas y una omitida de staging, 33
frontend, lint Python/JavaScript y build. Después del ajuste final de referencias
en borrador se repitieron 97 pruebas de aprendizaje, arquitectura e integraciones,
todas aprobadas. Se comprobó también la API real con las cuentas ficticias y la
semilla idempotente (34 creados, luego 34 conservados). El navegador continúa
bloqueando la inspección visual local; no se considera validada su apariencia.

Referencias de condiciones y enlaces actuales:

- [Microsoft Learn y sus preguntas frecuentes](https://learn.microsoft.com/en-us/training/support/faq)
- [Google Career Certificates](https://grow.google/certificates/)
- [Google Analytics Academy](https://support.google.com/analytics/answer/15068052)
- [HubSpot Academy: preguntas de certificación](https://knowledge.hubspot.com/help-and-resources/hubspot-academy-certification-frequently-asked-questions)
- [Cisco Networking Academy](https://www.netacad.com/)
- [freeCodeCamp: currículo de Python vigente](https://www.freecodecamp.org/news/freecodecamps-new-python-certification-is-now-live)
- [OpenLearn: comunicación en el trabajo](https://www.open.edu/openlearn/money-business/effective-communication-the-workplace/content-section-overview)
- [AWS: formación Cloud Practitioner](https://aws.amazon.com/training/learn-about/cloud-practitioner/)
- [CS50: condiciones del certificado](https://cs50.harvard.edu/x/certificate/)
- [IBM: análisis de datos](https://www.coursera.org/professional-certificates/ibm-data-analyst)
- [Rutgers: cadena de suministro](https://www.coursera.org/specializations/supply-chain-management)


## Formación en español y lectura de fuentes públicas — 10 de octubre de 2026

La biblioteca editorial contiene **65 recursos de 13 grupos de proveedores**:
55 de acceso gratuito y 10 de pago. Esta ampliación incorpora **19 programas
virtuales del SENA y 12 cursos en español de HP LIFE**. Cubre las diez áreas,
incluida atención y procesos en salud. Los temarios resumidos, requisitos,
certificación e ideas de evidencia están separados de los laboratorios locales.
Los cursos de HP LIFE tienen una reserva de estudio orientativa de 2 horas;
la ficha pública no publica una duración numérica. Sus certificados son de
finalización, sin acreditación educativa oficial.

En Mi desarrollo > Cursos y prácticas hay accesos a Gratis en español y SENA.
Los filtros avanzados incluyen idioma, modalidad, disponibilidad y certificado.
El detalle muestra edad mínima, cobertura, última consulta y condiciones.
Una inscripción anunciada no reserva una plaza. A los 14 días sin comprobación,
o si falla una actualización, la disponibilidad pasa a por confirmar.

Administración > Catálogo educativo permite buscar programas virtuales del
SENA por tema, revisar sus enlaces e importar una selección. Por defecto quedan
como borradores. El mapeo automático de habilidades es una sugerencia por título
que debe revisarse; no acredita conocimientos ni modifica perfiles. La consulta
está limitada a 20 programas y cacheada 24 horas. La importación reconoce un
curso ya incorporado editorialmente y conserva sus ediciones y planes.

Las convocatorias de Sapiencia se muestran en un bloque independiente, paginado
de cuatro en cuatro, con requisitos territoriales y filtro de estado. No se
convierten en cursos ficticios ni se les asignan horas inventadas. El candidato
solo lee la copia guardada en la base local.

Se implementó lectura de las páginas públicas de Betowa y Sapiencia, con hosts
fijos, comprobación de robots.txt, sin redirecciones, límites de tamaño/tiempo,
caché persistente y conservación de la última lectura si falla la fuente. No se
usaron APIs privadas, RSS supuestos, cuentas de alumnos ni contenido de pago.
Si cambia el HTML puede requerirse adaptar el lector. Las fuentes originales:
https://betowa.sena.edu.co/oferta y https://sapiencia.gov.co/convocatorias/.
HP LIFE es una selección editorial: https://www.life-global.org/es/allcourses
con condiciones revisadas en https://www.life-global.org/es/help.

La migración vigente es **0040_learning_sources**. Solo añade una caché pública;
no elimina tablas ni cuentas. Para repetir la carga y actualización local:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py setup
backend/.venv/Scripts/python.exe scripts/local.py seed-education
backend/.venv/Scripts/python.exe scripts/local.py sync-education
```

La actualización diaria se habilitó únicamente en `.local/backend.env` mediante
PUBLIC_LEARNING_REFRESH_ENABLED=true. Se ejecuta al arrancar y cada 24 horas
mientras el backend permanece abierto; si el equipo está apagado se recupera al
siguiente arranque. Solo revisa fichas del SENA ya guardadas y convocatorias de
Sapiencia. No publica nuevos cursos, no sobrescribe contenido editorial y no
consume servicios de pago. Los demás entornos la tienen desactivada por defecto.
Las consultas de candidatos no desencadenan conexiones externas. El refresco se
limita por cantidad, tiempo y fallos consecutivos; no constituye un crawler masivo.

Microsoft Learn mantiene su conector autenticado pendiente de acceso Entra.
YouTube Data API y catálogos comerciales siguen requiriendo configuración o
acceso autorizado; esta ampliación no simula una sincronización con ellos.


## Conector de listas públicas de YouTube · 10 de octubre de 2026

Administración > Catálogo educativo incluye un bloque desplegable para revisar
una lista pública por enlace o ID. Utiliza YouTube Data API v3 (`playlists.list`
y `playlistItems.list`), dos peticiones por revisión y una muestra de hasta doce
vídeos. No hay búsqueda masiva, OAuth de candidatos, descarga de vídeos,
reproducción incrustada, consultas al abrir el catálogo ni publicación automática.
Una muestra se identifica como tal y no se presenta como el temario completo.

El administrador redacta una ficha propia con título, utilidad, habilidades,
área, idiomas, nivel, tiempo de estudio, requisitos e idea de evidencia. La
importación se guarda como borrador por defecto y evita duplicar la lista.
Una lista no otorga certificación y su duración de estudio es una estimación
editorial, independiente de la duración de reproducción. Importar conserva
los cursos ya editados y sus planes. La publicación es una elección explícita.

Los metadatos de la API se muestran temporalmente durante quince minutos y no
se persisten en tablas, eventos ni tokens de vista previa. Solo se conserva el
ID de la lista junto con la ficha editorial y la fecha de revisión. Esto evita
crear una copia permanente de títulos, autores, descripciones o estadísticas
de YouTube. La vista previa está asociada al administrador, expira y está
limitada a 32 tokens por proceso. El navegador retira la consulta al vencer.

El servidor solo consulta el host fijo www.googleapis.com, sin redirecciones,
con tiempo/tamaño limitados y clave en cabecera, nunca en URLs ni respuestas.
No se envían datos de perfiles. El bloque explica el tratamiento y enlaza a
los términos de YouTube y la política de privacidad de Google.

Configuración en el archivo privado `.local/backend.env`, nunca en VITE_*:

```dotenv
YOUTUBE_LEARNING_ENABLED=false
YOUTUBE_API_KEY=
YOUTUBE_LEARNING_DAILY_REQUESTS=100
```

Para activar, habilitar YouTube Data API v3 en un proyecto propio de Google,
crear una clave restringida a esa API, escribirla únicamente en el archivo
privado, cambiar enabled a true y reiniciar el backend. El límite local cuenta
intentos, incluidos errores, y se reinicia a medianoche UTC. Es por proceso;
reiniciar o usar varios workers no sustituye la cuota del proyecto de Google.
Los tests desactivan esta configuración y usan respuestas simuladas aisladas.
Sin clave permanece inactivo; el formulario manual permite añadir enlaces.

Referencias oficiales:
https://developers.google.com/youtube/v3/docs/playlists/list
https://developers.google.com/youtube/v3/docs/playlistItems/list
https://developers.google.com/youtube/terms/developer-policies
https://docs.cloud.google.com/docs/authentication/api-keys-best-practices
