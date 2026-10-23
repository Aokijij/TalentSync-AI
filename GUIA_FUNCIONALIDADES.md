# TalentSync: funciones principales y cómo utilizarlas

Actualizado el 22 de octubre de 2026. Describe la versión local del proyecto. Una integración implementada puede requerir configuración y autorización antes de funcionar con cuentas externas.

La [revisión de estabilidad y listados](REVISION_PLATAFORMA.md) documenta las correcciones, comprobaciones reproducibles y límites de validación de esta versión.

TalentSync conecta tres recorridos: el candidato organiza su trayectoria y búsqueda; la empresa publica ofertas y gestiona la selección; administración revisa la calidad, las fuentes educativas y la salud del ecosistema.

## Novedad: comparar vacantes antes de postularse

**Dónde:** candidato → Explorar vacantes (`/vacantes`).

1. Pulsa **Comparar** en las acciones de dos o tres tarjetas. Puedes cambiar de filtro, colección o página sin perder la selección. La barra inferior muestra las vacantes seleccionadas y permite retirarlas o abrir la comparación; aparece después de elegir una oferta.
2. Pulsa **Comparar** en el bloque que reúne las ofertas elegidas.
3. Revisa salario, modalidad, ubicación o alcance remoto, contrato, horario, experiencia, formación, idiomas, beneficios y plazos.
4. Consulta la compatibilidad y las habilidades cumplidas o por reforzar/confirmar, cuando el cálculo dispone de ese detalle.
5. Activa **Mostrar solo condiciones diferentes** para concentrarte en las diferencias. Abre la oferta que quieras revisar antes de postularte.

**Ejemplo:** una oferta puede publicar 3 millones, contrato indefinido y modalidad híbrida; otra, 3,5 millones y trabajo remoto, pero sin contrato informado. La comparación permite ver el intercambio entre condiciones y qué falta preguntar.

La selección se conserva por cuenta en la misma pestaña durante la sesión; no es una colección sincronizada entre dispositivos. Guardar una vacante y seleccionarla para comparar son decisiones independientes. Si una oferta deja de estar disponible, puedes retirarla de la selección. Los datos desconocidos se presentan como tales: un salario ausente no se convierte en cero ni una compatibilidad sin calcular en 0 %. La herramienta no elige una ganadora.

En **Mercado laboral**, la compatibilidad mínima parte de **Cualquiera**: incluye las ofertas con un porcentaje bajo o todavía sin calcular. Las recomendaciones mantienen su mínimo del 40 %. Cada tarjeta presenta la compatibilidad con una barra y destaca las postulaciones enviadas, su estado y el acceso a **Ver mi proceso**. El detalle de la oferta conserva el mismo aviso; desde el seguimiento, **Ver vacante completa** abre sus condiciones y requisitos.

## Novedad: agenda de entrevistas y calendario

**Dónde:** candidato → Postulaciones (`/postulaciones`) → **Tu agenda de entrevistas**. También dentro de un proceso (`/procesos/{id}`), accesible a sus participantes autorizados.

- Reúne las entrevistas futuras de procesos abiertos y las ordena por fecha. Muestra primero tres; se pueden desplegar las restantes.
- La empresa programa, reprograma o cancela desde **Gestionar proceso**, la agenda de la vacante o el propio proceso. **Guardar y notificar** aplica la entrevista directamente, sin otro guardado en el tablero.
- Se definen fecha y hora de Colombia, modalidad virtual o presencial, duración, enlace HTTPS o dirección e indicaciones para el candidato. Los datos antiguos sin modalidad se identifican como pendientes de confirmar.
- **Añadir a Google Calendar** guarda el evento con esos detalles y un recordatorio 30 minutos antes. Una vez añadido, los cambios y cancelaciones se actualizan automáticamente. La conexión se autoriza una vez desde Seguridad; solo se pide renovarla cuando Google revoca o vence el permiso.
- Se retiró **Descargar cita** de la interfaz. El endpoint histórico de iCalendar permanece por compatibilidad.
- Cambiar fecha, modalidad, lugar o indicaciones genera una notificación y una entrada del historial. El contador de avisos se actualiza periódicamente mientras la aplicación está visible.
- El plazo de respuesta protege la entrevista y su periodo posterior. Vencer el compromiso activa seguimiento y avisos; el resultado de selección se comunica expresamente. El guardado conserva las comprobaciones de versión para evitar sobrescribir cambios de otro miembro del equipo.

También se corrigió la conversión de fechas: abrir una entrevista ya guardada y volver a guardar su hora no debe desplazarla cinco horas. Los avisos indican expresamente la hora de Colombia.

## Reciente: CV independiente para cada vacante

**Dónde:** detalle de una vacante → **Prepara tu postulación** → **CV por vacante**.

Esta función permite adaptar la presentación de una trayectoria real al cargo, conservando el perfil principal.

1. En **Contenido**, revisa el resumen y despliega experiencias o habilidades si quieres cambiar la selección.
2. Pulsa **Continuar al diseño**.
3. En **Diseño y guardado**, escribe un **Nombre del CV** (por ejemplo, «Frontend · React») y elige un diseño moderno, clásico o minimalista. La foto y los apartados visibles se toman de las preferencias guardadas del CV en tu perfil; para cambiarlos, ve allí y pulsa **Guardar diseño y preferencias**.
4. Guarda la versión. En **Versiones**, el nombre aparece junto a su fecha. Puedes **Renombrar** cualquier CV guardado, incluidos los anteriores, y abrir el PDF para revisarlo. Si no indicas un nombre, se asigna «CV 1», «CV 2», etc. El nombre es privado: permite organizar y elegir tus documentos sin alterar el PDF enviado a la empresa.
5. Pulsa **Usar al postularme** para seleccionarla. Después debes enviar la postulación desde su botón habitual.

**Ejemplo:** puedes destacar experiencia de pruebas y calidad para una vacante de QA, y experiencia de interfaces para una de frontend, sin borrar ninguna del perfil principal.

Guardar el documento no envía una postulación ni lo selecciona automáticamente. Antes de enviar desde el inicio, las recomendaciones o el detalle de una vacante, un modal permite responder sus preguntas y confirmar qué hoja de vida adjuntar: **Mi CV del perfil** (opción inicial), una versión guardada para la oferta o **Continuar sin adjunto**. Puedes revisar el PDF antes de confirmar.

Tanto el CV del perfil como una versión elegida se conservan como un PDF de esa postulación: editar después el perfil no cambia el archivo recibido por la empresa. La empresa autorizada ve **Descargar hoja de vida**, sin avisos sobre adaptaciones para la oferta. Sin adjunto, se comparte el perfil profesional y sus respuestas, sin ofrecer un PDF descargable. La visibilidad de identidad y los permisos del proceso se siguen aplicando.

En ofertas externas puedes preparar y descargar el CV; lo que envíes después en otro portal depende de la acción que realices allí. TalentSync no confirma una entrega externa.

## Reciente: preparación privada de entrevistas

**Dónde:** detalle de vacante → **Prepara tu postulación** → **Practicar entrevista**. Tras postularte: proceso → **Prepara tu entrevista**.

La preparación reúne preguntas relacionadas con la oferta y ejemplos de experiencias registradas. Prioriza habilidades esenciales y utiliza extractos de responsabilidades o requisitos de la vacante, que puedes desplegar junto a la pregunta. Cada habilidad incorpora puntos concretos para profundizar: por ejemplo, duplicados en SQL, pruebas en Python o validación de fórmulas en Excel. Puedes elegir una pregunta desde el selector y consultar ejemplos de tu trayectoria solo cuando los necesites. Puedes trabajar cada respuesta mediante cuatro apartados:

| Apartado | Qué escribir |
| --- | --- |
| Contexto | Qué estaba ocurriendo y cuál era el problema. |
| Responsabilidad | Qué te correspondía resolver a ti. |
| Acción | Qué hiciste concretamente y cómo lo hiciste. |
| Resultado | Qué cambió, qué entregaste o qué aprendiste. Puede ser cualitativo. |

Guarda tus notas para continuar después o descárgalas como texto. En una postulación nueva, la preparación puede consultar los datos conservados del envío, incluso si la oferta dejó de estar activa. Si cambió la información utilizada, se señala que las notas necesitan revisión. Un conflicto entre dos ventanas no debe sobrescribir silenciosamente lo guardado.

Las respuestas son privadas: no se muestran a la empresa ni alteran tu compatibilidad. La revisión actual comprueba si los cuatro apartados están completos; no califica tu capacidad ni verifica el contenido de tu respuesta. **Todavía no es un simulador conversacional con repreguntas automáticas.** Ese desarrollo sigue siendo una siguiente etapa.

## Funciones principales del candidato

**Cómo se realiza un reto:** al pulsar **Empezar práctica** o **Continuar práctica**, el catálogo se sustituye por un espacio de trabajo dedicado, situado al principio de la página. Incluye la pregunta actual, opciones con selección visible, tiempo restante y navegación entre preguntas. Al continuar un intento se recupera el borrador y se abre la primera pregunta pendiente; si todas están respondidas, se abre la revisión.

Antes de entregar puedes consultar todas las respuestas y editar cualquiera. La entrega requiere completar todas las preguntas y disponer de tiempo; la evaluación y el vencimiento siguen controlados por el servidor. Después se muestran el resultado y las explicaciones, con los puntos por reforzar desplegados y recursos relacionados cuando están disponibles.

**Salir y conservar respuestas** vuelve al catálogo; no pausa ni reinicia el tiempo. El borrador se conserva en esa pestaña del navegador. Si el navegador impide guardarlo, aparece un aviso y la página mantiene las respuestas en memoria mientras siga abierta. No se garantiza recuperarlas después de cerrar o recargar cuando el almacenamiento está bloqueado.

| Función | Para qué sirve |
| --- | --- |
| Perfil y hoja de vida | Organizar experiencia, formación, habilidades y niveles, idiomas, cursos, enlaces, foto y documentos profesionales. Exportar el CV con diferentes diseños. |
| Visibilidad de datos personales | Decidir qué datos personales se comparten según los controles del perfil. En la vista de empresa, cuando se comparte el dato correspondiente, se presenta la edad en lugar de la fecha de nacimiento. |
| Asesor de redacción | Revisar propuestas de descripción basadas en las experiencias registradas, editarlas y decidir si se aplican al perfil. Conserva versiones y permite deshacer mientras exista su registro. La generación depende de la disponibilidad del modelo configurado. |
| Recomendaciones y compatibilidad | Encontrar ofertas y consultar razones y requisitos relacionados con el perfil. Una afinidad académica compara datos declarados; no autentica un diploma. |
| Guardar y ocultar ofertas | Organizar oportunidades y, cuando se autoriza, utilizar esas decisiones explícitas para personalizar sugerencias. |
| Seguimiento de postulaciones | Consultar estado, etapas, plazos, historial y feedback comunicado por la empresa; retirar una postulación cuando el proceso lo permite. |
| Cursos y prácticas | Filtrar recursos, ver las habilidades que refuerzan y añadir actividades al plan personal. Completar un curso no acredita automáticamente dominio de una habilidad. |
| Mi plan y resultados | Continuar actividades iniciadas y consultar sus entregas o resultados, distinguiendo práctica, información declarada y evaluación disponible. |
| Radar laboral | Explorar habilidades solicitadas, perfiles comparables y salarios publicados. En Ubicación puedes elegir Todo el país o Una ciudad y pulsar Actualizar radar. Las comparaciones de perfiles y medianas salariales requieren área, nivel y muestra suficiente; Usar mi perfil recupera tu ciudad y los filtros sugeridos. La muestra corresponde a los datos disponibles en la plataforma y no representa todo el mercado laboral colombiano. |

## Funciones principales de la empresa

- **Vacantes y calidad de ofertas:** publicar y revisar condiciones, responsabilidades, habilidades, formación, documentos requeridos, preguntas y etapas de selección.
- **Búsqueda de talento:** consultar candidatos compatibles, revisar el detalle del ajuste y comparar candidatos dentro del alcance autorizado.
- **Postulaciones por volumen:** elegir una vacante y trabajar con Por revisar, Proceso activo, Entrevistas y Finalizados. La bandeja carga 25 candidaturas por página y permite buscar, ordenar por compatibilidad o fecha, filtrar sin revisar y distinguir puntuaciones ausentes. El panel lateral resume la etapa, la entrevista y el compromiso de respuesta. La hoja de vida se consulta mediante Ver perfil; las respuestas conservan su diálogo independiente. En móvil se usa una vista de detalle con regreso a la lista. Abrir una candidatura registra su revisión individual sin cambiar de etapa ni marcar al resto como visto.
- **Proceso activo:** contiene las candidaturas que avanzaron desde la recepción. Admite tablero con ocho candidatos iniciales por columna y carga adicional, o lista paginada. Mover una tarjeta o elegir una etapa abre una confirmación con la etapa actual, la etapa de destino y el aviso que recibirá el candidato. Cancelar no guarda ni notifica. El tablero y la lista permiten filtrar por etapa. Finalizar exige motivo y mensaje; la contratación se confirma expresamente. Se conservan las etapas personalizadas y los historiales. La etapa actual se muestra en las tarjetas y el detalle; el seguimiento muestra el recorrido de etapas.
- **Panel de candidatura:** prioriza programar, gestionar o registrar la entrevista realizada según su estado. Tras registrarla ofrece accesos directos a evaluar y comunicar la decisión. Historial y plazo abren su sección correspondiente del proceso. Cambiar etapa despliega el selector; contratar y finalizar se agrupan en Decidir, conservando las confirmaciones y el feedback obligatorio. Los procesos finalizados son de solo lectura.
- **Gestión de entrevistas:** programar o cancelar la fecha, comunicar cambios y registrar evaluaciones internas según los permisos del equipo. **Gestionar proceso** contiene la entrevista y las notas internas, con guardado directo. **Respuestas de postulación** se abre por separado y presenta una pregunta cada vez; la valoración se guarda desde ese diálogo. La nueva bandeja no necesita un guardado global posterior.
- **Seguimiento transparente por secciones:** abre un resumen con la etapa actual, entrevista, último mensaje y plazo de respuesta. El contexto y las responsabilidades de la vacante, la evaluación interna, el historial y la comunicación se consultan en pestañas separadas. Cambiar de pestaña conserva los borradores mientras la página siga abierta; recargar o salir no guarda formularios pendientes. El candidato no recibe las evaluaciones privadas del equipo.
- **Responsabilidades legibles:** el contexto se presenta en párrafos y las tareas con viñetas se convierten en listas, sin generar funciones nuevas. Los requisitos se muestran aparte y las condiciones de la oferta se pueden desplegar.
- **Compatibilidad al valorar respuestas:** el diálogo utiliza la misma base calculada para el tablero y muestra base del perfil actual, ajuste de respuestas y compatibilidad proyectada. No vuelve a sumar los puntos sobre un porcentaje ya ajustado. Si el dato todavía no llegó, lo consulta; si falla, permite reintentarlo conservando la valoración. La proyección es privada y se aplica únicamente al guardar.
- **Perfil del candidato y CV enviado:** consultar información compartida y, cuando corresponde, el documento conservado de esa postulación. Las notas privadas de preparación pertenecen al candidato.
- **Organización y equipo:** gestionar miembros, roles y vacantes asignadas. Un entrevistador no recibe acceso general a todos los procesos.
- **Feedback y confianza:** comunicar avances o resultados y consultar incidencias relacionadas con la organización.

Los atajos de la lista son ↑/↓ para navegar, A para avanzar a la etapa elegida y R para abrir la finalización con feedback. Se desactivan al escribir o gestionar un modal. Ninguna puntuación descarta candidatos automáticamente. La lista usa las compatibilidades ya guardadas; cuando falta una se puede calcular para el perfil seleccionado sin ejecutar cientos de cálculos al abrir la vacante.

La primera entrega de esta propuesta no incorpora todavía entrevistas múltiples por postulación, rúbricas por criterio, agregación de evaluaciones ni reserva automática de horarios. La sección Entrevistas reúne las próximas citas de la vacante y reutiliza la gestión y sincronización actuales.

## Funciones principales de administración

- Gestionar usuarios, organizaciones y verificaciones dentro del alcance administrativo.
- Revisar comportamiento de empresas e incidencias del ecosistema.
- Mantener el catálogo educativo: revisar fuentes, importar recursos y relacionarlos con habilidades demandadas.
- Consultar disponibilidad del motor y las integraciones. Tener un adaptador implementado no demuestra que sus credenciales, cuota o servicio estén funcionando.

## Qué sigue pendiente de las propuestas

Las cartas de presentación, el simulador conversacional y el seguimiento de postulaciones externas mediante correo autorizado siguen siendo propuestas. La sincronización con Google Calendar y el panel unificado de integraciones ya están implementados; requieren configuración y comprobación externa donde corresponda. La migración 0047 corrige las diferencias históricas del esquema. Siguen pendientes la configuración y verificación externa de proveedores, ejecutar el piloto y completar las pruebas de carga y la operación en staging.

Breken y Figma no están conectados. Las referencias de diseño se utilizan para mejorar los componentes existentes; no se incorporaron nuevas dependencias de animación o 3D.

## Registro y acceso con proveedores

Google y GitHub comparten el flujo de registro e inicio de sesión de candidatos. LinkedIn se retiró del acceso por ahora. Cuando se configura un proveedor, aparece en ambas pantallas. Una cuenta nueva pasa por la bienvenida para completar su perfil; una cuenta que regresa conserva sus datos. Si el correo ya existe por otro método, se entra con ese método y se vincula el proveedor desde Seguridad. Las cuentas no se fusionan automáticamente y se conserva el segundo factor cuando está activo.

Seguridad muestra el proveedor con su icono, estado de conexión y acción para vincular o desvincular. Vincular requiere demostrar acceso a TalentSync y autorizar la cuenta en el proveedor. Si la cuenta se creó con acceso social y no tiene contraseña conocida, se establece mediante Recuperar acceso antes de gestionar otras vinculaciones.

Google y GitHub están habilitados en el entorno local. Google ya completó un acceso real y Google Calendar quedó conectado, con renovación de token y respuesta de su API comprobadas. La prueba real de GitHub queda para el propietario. LinkedIn ya no aparece en los controles de acceso; el correo externo todavía requiere configuración. La configuración privada, los callbacks y los pasos de cada proveedor están en [INTEGRACIONES_ACCESO](INTEGRACIONES_ACCESO.md). La aparición de los botones no demuestra un consentimiento real completado.

Las pruebas de lógica, permisos y compilación se complementan con una suite visual de componentes: **24 casos ejecutados con Chromium**, en tres roles, dos temas y cuatro tamaños. Se inspeccionaron capturas representativas y se corrigieron detalles de espaciado y datos ausentes. Esta comprobación con datos ficticios no sustituye una revisión completa de todas las pantallas con cuentas autenticadas ni una comparación automática con capturas de referencia.

La revisión posterior recorrió **140 vistas autenticadas y 18 flujos funcionales** con el frontend y la API locales completos, sobre una copia aislada y cuentas de demostración. Incluye entrega de retos, conservación de respuestas, PDF del CV, edición de ofertas, borradores privados y comunicación de avances entre empresa y candidato. El alcance y los resultados se describen en `REVISION_PLATAFORMA.md`.


## Avisos, confirmaciones y estado de conexiones

- Los avisos distinguen información, éxito, advertencia y error. Los errores no desaparecen automáticamente por tiempo; los avisos temporales pausan su cierre mientras tienen el foco o el puntero. Los cálculos, búsquedas y vistas previas no anuncian que se guardaron cambios.
- Las confirmaciones aparecen encima de otros modales, permiten volver a la edición y enfocan primero la opción de cancelar. Las eliminaciones tienen una presentación distinta y describen su alcance.
- Mi perfil indica cuándo hay ediciones pendientes, evita envíos simultáneos y ofrece Cancelar edición. Descartar recupera el perfil guardado; un fallo al guardar conserva los campos. Al recargar o cerrar una pestaña con cambios pendientes se utiliza el aviso del navegador.
- Motor e integraciones permite buscar y filtrar conexiones. Separa configuración de resultados: último intento, última operación correcta, error y registros de más de 24 horas. Las consultas de fuentes educativas y sincronizaciones de vacantes registran resultados sanitizados desde esta versión; no se reconstruye historial inexistente. Las operaciones pueden usar caché, y consultar el panel no ejecuta pruebas externas.
- La regresión visual compara 36 capturas de componentes compartidos. Su ejecución y revisión se describen en `frontend/quality/README.md`.

## Calendario, datos de cuenta y operación

- **Seguridad → Calendario:** autoriza Google Calendar por separado del inicio de sesión. Desde una entrevista, elige duración de la copia y sincroniza; cambios y cancelaciones se actualizan con reintentos. No se añaden invitados ni notas internas. Desconectar conserva los eventos ya copiados en Google. Requiere configurar el cliente OAuth del entorno.
- **Seguridad → Mis datos:** descarga ZIP con datos propios y CV, o solicita eliminar la cuenta con contraseña, segundo factor si está activo, texto ELIMINAR y confirmación. Los fallos de limpieza de archivos quedan pendientes y se reintentan. Una cuenta propietaria de organización debe transferir propiedad; debe quedar otro administrador.
- **Administración → Motor e integraciones → Operación y correos:** consulta base, archivos, configuración de Calendar, limpieza, conservación, p95/errores y entrega de correo. Aceptado por el proveedor y entregado son estados distintos; los webhooks firmados de Resend confirman entrega/rebote, SMTP no confirma recepción.
- **Evaluación de calidad:** [protocolo y herramienta](docs/PROTOCOLO_PILOTO.md) para recorridos, extracción y relevancia con datos sintéticos. El piloto real queda pendiente de consentimiento y muestra autorizada.

[Configuración y límites operativos](docs/OPERACION_Y_DATOS.md). Estas funciones no implican una conexión externa verificada, publicación en nube ni validación con personas reales.


### Seguimiento de entrevistas y cierre de candidaturas

- **Programadas:** citas futuras con fecha, modalidad, duración y enlace o dirección.
- **Por registrar:** la hora ya pasó y la empresa debe confirmar si la entrevista se realizó o reprogramarla. El paso del tiempo no confirma asistencia.
- **Pendientes de respuesta:** la empresa registró expresamente que la entrevista se realizó. Se guarda la fecha de confirmación, se notifica al candidato y comienza el plazo para responder. La evaluación interna sigue separada del mensaje comunicado.
- Una reprogramación reinicia la confirmación de asistencia y conserva el evento anterior en el historial. Un avance posterior saca la candidatura del grupo de decisiones de entrevista pendientes.
- Los procesos finalizados conservan respuestas y evaluaciones en modo de consulta. No permiten gestionar entrevistas, modificar valoraciones ni reactivarse al reabrir la vacante.
- Google Calendar muestra un acceso de conexión legible y compacto. Conectar la cuenta y añadir una entrevista son acciones distintas; solo las entrevistas añadidas se actualizan con sus cambios.


### Compromisos de respuesta y seguimiento de retrasos

La duración estimada de selección se muestra separada del próximo compromiso de respuesta. Las nuevas ofertas proponen cinco días laborables por avance; la empresa puede ajustar entre 1 y 30. Los nuevos plazos se calculan de lunes a viernes en hora de Colombia, sin descontar festivos. Las fechas previamente acordadas se conservan hasta un avance o una ampliación explícita, salvo la protección necesaria por una entrevista.

1. Antes de vencer, se recuerda el compromiso al responsable de selección.
2. Al vencer, se registra **Respuesta atrasada** y se avisa a empresa y candidato. La etapa, la candidatura y el último feedback de la empresa se conservan.
3. Si pasan tres días laborables desde el aviso sin respuesta, el proceso aparece en **En pausa**. Se conserva su historial y no se convierte en un descarte.
4. La empresa puede ampliar una vez por etapa, con motivo público y nueva fecha. La ampliación añade hasta siete días laborables al compromiso actual, o desde hoy si venció. Requiere confirmar el aviso al candidato y respetar la entrevista programada.
5. Un avance real o la gestión de una nueva fecha de entrevista establece su compromiso correspondiente. Guardar notas, valorar respuestas, abrir perfiles o repetir la misma etapa no reinicia el plazo.

El seguimiento muestra responsable, fecha comprometida, estado del plazo y fecha de pausa prevista. Las pausas se consultan en su propia sección de postulaciones; desde allí puede retomarse con nuevo compromiso o comunicarse una decisión. Las ampliaciones y los avisos se registran en el historial. El incumplimiento se conserva en los indicadores de respuesta incluso si luego se amplía el plazo. Los cierres históricos ya comunicados conservan su resultado.
