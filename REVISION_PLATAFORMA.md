# Revisión de estabilidad y listados

22 de octubre de 2026. Alcance: versión local, pruebas con datos ficticios y bases aisladas. Los resultados de cada ejecución se registran en `.local/verification/platform-review.json`; no se publican credenciales ni datos de cuentas.

## Cambios revisados

- **Vacantes:** Mercado laboral parte de **Cualquiera** y permite incluir porcentajes bajos o pendientes de cálculo. Las recomendaciones conservan su mínimo de 40%. Se normalizan enlaces antiguos y números de página inválidos. El filtro conserva la página solicitada durante la carga y ajusta el rango cuando llegan los resultados. Si se elige un umbral concreto y falla el cálculo, se ofrece continuar sin aplicarlo mediante una acción explícita.
- **Postulaciones:** páginas de ocho registros, navegación a la página de una postulación enlazada y conteos que excluyen procesos liberados o cerrados. Una retirada no se presenta como un rechazo de la empresa. El estado de carga se mantiene separado de un listado vacío.
- **Administración:** las respuestas anteriores de búsquedas y páginas se cancelan o descartan. La tabla y sus totales corresponden a la misma consulta; una respuesta tardía no sobrescribe otra pestaña. Las eliminaciones que vacían la última página permiten volver a un rango válido.
- **Notificaciones:** cambios de categoría con cancelación de consultas, prevención de cargas simultáneas, deduplicación por identificador y cursor basado en filas consumidas del servidor. Tras borrar o marcar como leído se actualiza la consulta para evitar omisiones. Una carga fallida no se presenta como «Estás al día».
- **Formación:** el área seleccionada determina qué catálogo puede mostrarse; una carga o error no deja visibles los cursos del área anterior. Un precio ausente se muestra como pendiente de confirmar y queda fuera del filtro de gratuitos.
- **Retos:** consultar un resultado histórico no sustituye un intento más reciente. La versión y la fecha del intento determinan qué estado se presenta en el catálogo.
- **Compatibilidad:** el tablero distingue una valoración pendiente de guardar del resultado persistido. Las invitaciones respetan el umbral profesional de 50% del servidor, diferente del mínimo de búsqueda de 40%, y explican los bloqueos por preferencias o invitaciones pendientes.
- **Valoración desde Buscar talento:** la respuesta incluye la versión actual de la postulación; guardar con una versión antigua provoca un conflicto en lugar de sobrescribir los cambios del equipo.

## Limpieza

Se retiraron componentes sin referencias en la aplicación: envoltorios antiguos de botón, campo y métrica; acceso antiguo al asesor; vista previa HTML anterior del CV; pantalla SQL retirada y prototipo de llamada sin interfaz. La exportación y vista previa actuales utilizan el PDF; el ejecutor SQL y los servicios de entrevista del backend se conservan.

Se eliminó el filtro local de búsqueda de talento que duplicaba la búsqueda vigente del servidor. Se conservaron las comparaciones de habilidades utilizadas por las tarjetas. La paginación comparte cálculo de rango, tamaño y páginas. Las pruebas de las vistas retiradas se sustituyeron por comprobaciones de las pantallas y utilidades vigentes.

ESLint detecta ahora tanto variables sin usar como referencias inexistentes. README y el plan de carrera se actualizaron para reflejar el CV por vacante, el mínimo de búsqueda y la existencia de la suite visual.

## Comprobaciones reproducibles

| Comprobación | Comando / informe |
| --- | --- |
| Backend y recorridos API | `backend/.venv/Scripts/python.exe scripts/local.py test` |
| Lógica y renderizado frontend | `cd frontend` → `npm test` |
| Análisis y compilación | `npm run lint`, `npm run build`, Ruff y `pip check` |
| Componentes de revisión visual | `npm run quality:ui:build`, `npm run quality:ui:list` y `npm run quality:ui` |
| Modelo de compatibilidad | `backend/.venv/Scripts/python.exe scripts/local.py model-check` |
| Extracción local de entidades del CV | `backend/.venv/Scripts/python.exe scripts/local.py cv-model-check` |
| PostgreSQL y recuperación | `backend/.venv/Scripts/python.exe scripts/staging_postgres.py check` |
| Integridad y disponibilidad local | `backend/.venv/Scripts/python.exe scripts/local.py doctor` |

El ensayo de PostgreSQL usa bases nuevas en el clúster local reservado para pruebas, comprueba el rol sin permisos administrativos y compara todas las filas tras restaurar. No ejecuta migraciones ni restauraciones sobre la base de trabajo o producción. La prueba PostgreSQL se omite en la suite SQLite y se ejecuta por este recorrido separado.

## Comprobación visual con Chromium

La suite de componentes se ejecutó con Chromium 158.0.8119.0: 24 combinaciones de candidato, empresa y administración; temas claro y oscuro; anchos de 360, 768, 1280 y 1440 píxeles. Comprueba desbordamiento de página, dimensiones de tarjetas y modales, comparación de vacantes, navegación por teclado, conservación de borradores, valoración de respuestas y el recorrido de los retos.

La inspección de capturas detectó que el espaciado del contenido de cursos solo se aplicaba dentro de una vacante. Se extendió a todas las tarjetas compactas y se añadieron comprobaciones de sus márgenes. También se corrigió la etiqueta de ubicación ausente y se evita mostrar un porcentaje de compatibilidad inventado cuando falta el dato.

La configuración admite `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` o una preferencia local en `.local/playwright-browser.json` con la propiedad `executablePath`. La variable de entorno tiene prioridad. Ese archivo queda fuera de Git; cada equipo puede usar su navegador sin modificar el código compartido. Si no se especifica ninguno, Playwright utiliza su navegador habitual. Las pruebas usan dos procesos para limitar la carga del equipo. Antes de ejecutarse, se compila la página de prueba y se sirve esa compilación fija: las recargas del servidor de desarrollo no pueden reiniciar un recorrido a mitad.

Para repetir desde PowerShell, dentro de `frontend`:

```powershell
# Solo si no existe la preferencia local:
$env:PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH = 'C:\ruta\al\navegador\chrome.exe'
npm run quality:ui
```

El informe interactivo se genera en `frontend/playwright-report/index.html`. Los resultados locales y las capturas representativas se describen en `.local/verification/visual-chromium.json`. Los datos de esta página de prueba son ficticios y se bloquean las consultas externas y a la API.

## Recorrido de pantallas autenticadas

Se revisaron 35 rutas de la aplicación con sesiones de candidato, empresa y administración: 140 vistas entre escritorio de 1440 píxeles y móvil de 360 píxeles, en los temas claro y oscuro. Este recorrido utiliza el frontend completo y la API local real, sin simular sus respuestas. La base y los archivos se copiaron a un entorno desechable; las escrituras se realizaron con cuentas de demostración, fuera de la base de trabajo. Las cuentas personales 20 y 72 se conservaron.

La cobertura incluye perfil, vacantes y sus detalles, empresas, recomendaciones, postulaciones y seguimiento, desarrollo profesional, notificaciones, confianza, seguridad, selección de candidatos, tablero empresarial, editor de ofertas, organización, administración, catálogo educativo, ecosistema, verificaciones y estado de integraciones. Las capturas se complementaron con 18 recorridos funcionales: filtros y plan de formación; inicio, conservación y entrega de retos; preparación de entrevista; comparación y PDF del CV; conteos y notas del tablero; edición y creación de borradores; comunicación y privacidad entre roles; fuentes educativas; seguridad y cierre de sesión; paginación y búsqueda en los tres roles.

Se corrigieron los desbordamientos de seguridad con correos largos, la paginación móvil de vacantes empresariales y las tarjetas de gráficos de administración. Se eliminó la duplicación de la región principal de los paneles de inicio. Al iniciar o entregar un reto ya no aparece el aviso genérico de cambios guardados sobre las preguntas; los errores y el resultado se muestran en el propio espacio de práctica.

También se retiraron unas 440 líneas del formulario y la previsualización antiguos de vacantes: sus controles de apertura ya conducían al editor guiado actual. Se comprobó que este editor guarda cambios, los conserva al recargar y permite crear un borrador que permanece oculto para los candidatos. El panel administrativo distingue ahora las contrataciones totales de las postulaciones asociadas a recomendaciones; no las presenta como una atribución causal o un mismo embudo.

El resumen privado, el inventario de vistas y las capturas están en `.local/verification/authenticated-ui.json` y `.local/authenticated-review/`. Las 213 pruebas frontend, ESLint y la compilación se ejecutaron sobre los cambios finales. No hubo cambios de backend en esta revisión.

## Ajustes de Mercado laboral y seguimiento

Mercado laboral incorpora **Cualquiera** como mínimo inicial, sin cambiar el umbral de las recomendaciones. Las tarjetas muestran porcentaje y barra de compatibilidad, acciones alineadas para guardar, ocultar y comparar, y el estado de postulación con acceso al proceso. La selección para comparar permanece en una barra inferior compacta. En seguimiento, un botón abre la vacante completa en lugar de repetir sus condiciones en un desplegable.

Se comprobaron 215 pruebas frontend y 24 recorridos visuales de componentes. Además, el frontend completo y la API local se probaron en móvil y escritorio, con ambos temas: filtros, guardar y desguardar, ocultar y restaurar, comparación y navegación entre postulación, proceso y vacante. Estos recorridos utilizan una copia desechable de los datos. El informe privado está en `.local/verification/market-vacancies.json` y las capturas en `.local/market-review/`.

## CV y confirmación de postulaciones

Inicio, recomendaciones y detalle de vacante comparten la confirmación previa: preguntas de la oferta y elección del documento antes de enviar. Se puede adjuntar el CV del perfil, una versión guardada o continuar sin PDF. Los nuevos envíos conservan el PDF del perfil o de la versión seleccionada; su descarga requiere autorización sobre el proceso. Las postulaciones históricas con datos conservados pueden generar el documento desde esos datos, sin utilizar ediciones posteriores del perfil.

La foto y los apartados del CV por vacante respetan las preferencias guardadas del perfil. La preparación oculta los controles de apartados excluidos y dirige sus cambios al perfil. La empresa recibe una descarga con un nombre normal de hoja de vida, sin avisos de adaptación a la oferta. El encabezado tiene menos espacio vacío y mantiene visible el perfil si falla una descarga.

Las verificaciones específicas incluyen permisos de descarga, ausencia de PDF al elegir no adjuntarlo, conservación del documento, preferencias y solicitudes repetidas. El modal se comprobó con ambos temas en móvil y escritorio; las capturas y el resumen privado se guardan en `.local/application-cv-review/` y `.local/verification/application-cv-flow.json`.

## Límites de la revisión

- Se comprobaron las rutas principales con cuentas de demostración y una selección representativa de capturas. Desde la consolidación posterior hay 36 referencias versionadas de componentes, avisos y confirmaciones. Los recorridos no cubren todas las combinaciones posibles de datos, permisos de miembros de equipo, dispositivos o navegadores.
- Correo externo, OAuth/SSO, calendarios sincronizados y otros proveedores requieren cuentas y configuración autorizadas. Las pruebas de adaptadores o transportes locales no equivalen a comprobar una entrega o conexión externa real.
- Las pruebas de concurrencia usan datos sintéticos. No representan una certificación de capacidad o una auditoría de producción.
- No se publicaron cambios ni se alteraron cuentas personales para realizar esta revisión.


## Consolidación de componentes, regresión visual e integraciones

Filtros de formación y radar, tarjetas de vacantes y cursos, pies de acciones y avisos utilizan geometría compartida. Se retiran reglas antiguas de tarjetas compactas y el inventario de conexiones que duplicaba el servicio vigente.

Las confirmaciones usan un diálogo nativo para funcionar sobre otros modales. El foco inicial está en cancelar; Escape conserva la edición. Los avisos distinguen tono, permiten cierre y pausa, evitan mensajes repetidos y evitan el cierre por tiempo de los errores. Perfil permite cancelar ediciones con confirmación y recuperar los datos guardados; un fallo conserva los campos. La protección de recarga/cierre no bloquea toda navegación interna de la aplicación.

El panel de conexiones muestra hechos separados: configuración, último intento, última operación correcta, problema registrado y antigüedad. YouTube, Microsoft Learn, SENA, Sapiencia y catálogos de vacantes aportan observaciones persistidas durante operaciones autorizadas. Los errores se traducen a categorías públicas; no se guardan tokens, respuestas del proveedor ni datos personales. Los proveedores sin observaciones continúan como sin comprobar. Consultar estado no consume cuotas. La aceptación del transporte de correo no se presenta como entrega.

Se incorporan 36 referencias visuales versionadas y un trabajo Windows de CI con Chromium fijado por Playwright. Cubren componentes, confirmaciones y avisos en tres roles, dos temas y dos tamaños; los recorridos funcionales conservan su cobertura de cuatro anchos. Los resultados locales de esta revisión se guardan en `.local/verification/platform-polish.json`. Esto no demuestra una ejecución del CI remoto ni una conexión externa real.

## Revisión previa y cuatro bloques posteriores

Se corrige el registro de operaciones sin comprobaciones (`checked: 0`), la lectura de fechas con zona horaria y la detección de rol de avisos sin foco en un panel. La página de pruebas ahora carga también las dos hojas de estilo globales que faltaban; las capturas reflejan los mismos estilos que la aplicación.

Se implementan eventos firmados de entrega de Resend, conexión delegada y sincronización de entrevistas con Google Calendar, exportación/borrado de datos propios, limpieza durable con arrendamientos, protocolo de piloto sin documentos personales y panel operativo de dependencias, colas y métricas acotadas. Hay tres migraciones nuevas; SQLite conserva los registros y evita reutilizar ID de cuentas borradas mientras se limpian archivos. Los controles de borrado no eliminan organizaciones ni la última cuenta administradora.

El protocolo se encuentra en [PROTOCOLO_PILOTO](docs/PROTOCOLO_PILOTO.md) y la configuración en [OPERACION_Y_DATOS](docs/OPERACION_Y_DATOS.md). El ejemplo de evaluación es sintético y no acredita calidad con personas reales. No se conectaron cuentas de Google ni se enviaron correos externos. No se publicaron recursos en nube.

En aquella entrega, la comparación global de metadatos con Alembic detectó diferencias históricas: nulabilidad de campos JSON/fecha, longitud del enum de estados en SQLite y un índice de offer_feedback ausente del modelo. La corrección posterior se recoge en la sección siguiente y en la migración 0047.

Validación de esta entrega: suite general con 1.082 pruebas backend aprobadas y una aceptación PostgreSQL reservada para el ensayo aislado; 218 pruebas frontend; 46 recorridos de interfaz; 12 comprobaciones de capturas que comparan 36 referencias sin regenerarlas; cuatro revisiones adicionales de la pantalla completa de Seguridad con datos interceptados. Tras reforzar la concurrencia del calendario y la finalización de limpieza, se repitieron 64 pruebas de los módulos afectados, todas aprobadas. ESLint, Ruff y compilación aprobados.

El ensayo PostgreSQL 18 aplica migraciones, prueba flujos y concurrencia, y compara las 35 tablas tras restaurar el respaldo. La recuperación de archivos usa dos documentos sintéticos y verifica sus hashes. El servidor local responde en liveness/readiness; 40 comprobaciones de readiness con cuatro conexiones terminaron sin errores (p95 aproximado de 31 ms). Este dato no mide extracción de CV, matching, vídeo ni capacidad en nube. Se verificó el respaldo SQLite antes de aplicar las migraciones y se conservaron los recuentos de las tablas existentes. Los informes privados quedan en `.local/operations/`, `.local/staging/verification.json` y `.local/final-targeted-tests.log`.

## Alineación del esquema y preparación de acceso social

La migración `0047_schema_alignment` normaliza colecciones SQL NULL y JSON null a listas vacías, conserva los contenidos existentes, completa las fechas de actualización ausentes y aplica los contratos NOT NULL del modelo. Amplía el estado de postulaciones en SQLite y conserva el enum nativo de PostgreSQL. El modelo declara el índice existente de feedback de ofertas. Las pruebas nuevas comprueban upgrade/downgrade, conservación de datos, estados largos, AUTOINCREMENT y la comparación global de Alembic. El ensayo PostgreSQL incorpora `alembic check` antes y después de downgrade/reupgrade.

Registro e inicio de sesión comparten los proveedores habilitados. Seguridad incorpora iconos y estados visibles de conexión. La revisión de interfaz usa las pantallas reales y datos sintéticos en móvil/escritorio y ambos temas, sin conectar cuentas ni salir a proveedores. Cubre errores recuperables, registro por correo, separación del registro empresarial y redirección aunque el navegador impida recordar el método.

`scripts/local.py integrations --init` prepara `.local/integrations.env` sin sobrescribir archivos existentes. La activación es explícita, no hereda secretos de la consola y nunca se carga en las pruebas aisladas. Admite credenciales sociales, Calendar y un transporte de correo. Los mensajes locales existentes permanecen locales. El remitente de pruebas Resend no se admite como remitente del registro general. El informe de configuración muestra callbacks y estados sin claves ni llamadas externas.

El propietario indicó que aún no tiene aplicaciones OAuth ni dominio y solicitó preparar los pasos. [INTEGRACIONES_ACCESO](INTEGRACIONES_ACCESO.md) documenta esa preparación. Google/GitHub pueden comprobarse en loopback HTTP; LinkedIn requiere HTTPS. La conexión real, el consentimiento de cuentas autorizadas y la entrega externa quedan pendientes de configuración. No se crearon recursos en nube ni se enviaron correos en esta entrega. Los resultados de las pruebas se conservan en `.local/schema-tests.log`, `.local/auth-integration-tests.log`, `.local/social-access/` y `.local/staging/verification.json`.

### Activación local posterior de Google, GitHub y Calendar

El propietario proporcionó después las credenciales. Se guardaron exclusivamente en el archivo privado ignorado por Git y se habilitaron Google, GitHub y Google Calendar, conservando desactivado el correo externo. LinkedIn continúa pendiente. La API reiniciada responde en liveness/readiness; sus opciones públicas habilitan Google/GitHub y los endpoints de inicio generan callbacks locales, estado de un solo uso y PKCE. La autorización de Calendar conserva su cliente y consentimiento separados.

Se comprobaron las pantallas reales de login y registro contra la API local, sin respuestas simuladas: ambos proveedores aparecen activos. No se completó un consentimiento externo ni se intercambiaron códigos de autorización; los callbacks deben coincidir en las consolas de los proveedores. Las comprobaciones de esta configuración están en `.local/google-github-calendar-activation.json` y `.local/social-activation/ui-verification.json`. La validación completa de código y esquema corresponde a la versión `7491056`; esta activación solo cambia configuración privada y documentación, sin incluir claves en el repositorio.

### Acceso social, Calendar y diseño de Seguridad: 23 de octubre de 2026

Esta revisión posterior completa dos inicios de sesión reales con Google y la conexión autorizada de Google Calendar. El bloqueo 403 de Calendar correspondía al proyecto en pruebas sin usuarios de prueba; se añadió la cuenta autorizada del propietario, manteniendo la aplicación en pruebas. Después del consentimiento explícito se comprobó la conexión guardada, la renovación del token y una respuesta HTTP 200 de Calendar solicitando únicamente el tipo de recurso. No se solicitaron contenidos de citas ni se crearon, modificaron o eliminaron eventos. No se habilitó facturación ni publicación pública.

La causa original del fallo de acceso social no se pudo aislar de forma concluyente. El flujo actual de Google quedó comprobado en el navegador. Se distinguen errores de estado, navegador, configuración, proveedor e identidad con referencias públicas acotadas, sin registrar códigos, tokens, correos ni respuestas privadas. El transporte solo reintenta establecer la conexión; no repite el intercambio tras un tiempo de espera de lectura. Se conservan PKCE, estado de un solo uso, validación de identidad y vinculación explícita. Las sesiones sociales registran el proveedor utilizado. El propietario pospuso la prueba real de GitHub; sus recorridos automatizados de vinculación y acceso posterior pasan para ambos proveedores.

Los botones de Google y GitHub ocupan una fila compacta en acceso y registro. Correo electrónico muestra su estado y abre el formulario solo al solicitar un cambio; un fallo conserva el nuevo correo y vacía la contraseña. La dirección actual se mantiene hasta confirmar el enlace. LinkedIn se retira de opciones públicas, botones y resumen de integraciones de acceso; los enlaces profesionales del perfil y el adaptador histórico permanecen conservados.

Validación: 69 pruebas backend de acceso, seguridad y calendario, más 6 de observación de integraciones; 220 pruebas frontend; 11 recorridos de interfaz en móvil/escritorio y ambos temas. Ruff, ESLint y compilación aprobados. Se revisaron capturas y las pantallas reales de acceso y registro contra la API local. Los resultados privados están en `.local/social-access-final-tests.log`, `.local/social-integration-readiness-tests.log`, `.local/social-final-frontend-tests.log`, `.local/calendar-live-verification.json` y `.local/social-access/`. Las credenciales, capturas personales y resultados locales quedan fuera de Git. La entrega de correo externo y el ciclo completo de eventos reales de entrevista no se han verificado en esta revisión.

### Entrevistas, seguimiento y controles de cuenta

La entrevista se guarda desde el propio modal con «Guardar y notificar»; ya no requiere un segundo guardado del tablero. Los errores se muestran sin perder el formulario. El encabezado y las acciones permanecen visibles mientras se recorre su contenido. La agenda de la vacante permite buscar candidatos y gestionar citas; el proceso también ofrece acceso directo para programarlas. Se conservan los movimientos pendientes de otros candidatos y las comprobaciones de versión. Escape cierra el selector de hora sin descartar todo el modal.

La migración `0048_interview_details` añade modalidad, duración, enlace o dirección e indicaciones compartidas, conservando las fechas existentes. Las citas antiguas no reciben una modalidad inventada. El backend valida los datos y enlaces HTTPS, rechaza fechas nuevas en el pasado y entrevistas nuevas o modificadas en procesos finalizados. Una entrevista futura mantiene el plazo de respuesta al menos hasta su final más los días de respuesta de la vacante, evitando cierres antes de celebrarla.

Cambios de fecha, modalidad, acceso o indicaciones generan notificación y un evento de historial. El registro de auditoría conserva solo acción, fechas, modalidad y duración; no almacena enlaces ni indicaciones libres. El contador de notificaciones se actualiza cada 30 segundos mientras la aplicación está visible y al recuperar el foco. Los cambios de entrevista no anuncian falsamente un cambio de etapa.

Google Calendar recibe duración, modalidad, empresa, enlace o dirección e indicaciones, además del vínculo al proceso y recordatorio. La duración declarada por la empresa prevalece sobre los valores históricos. Se retiró «Descargar cita» de la interfaz y el selector de «duración de la copia». La conexión sana muestra su estado y fecha, con la desconexión como acción secundaria; renovar se ofrece solo cuando el permiso necesita recuperarse. Control de tus datos separa descarga y eliminación; la comprobación de identidad se abre al elegir una acción y conserva la confirmación de borrado.

Validación: 77 pruebas backend de API, entrevistas, calendario, historial, organizaciones, migraciones y control de datos; 220 pruebas frontend; 32 recorridos funcionales de interfaz en tres roles, ambos temas y cuatro anchos. Los recorridos específicos de entrevistas y controles se repiten tras los últimos ajustes del modal. Ruff, ESLint y compilación aprobados. Antes de migrar la base local se verificó un respaldo; después se comprobaron integridad, recuentos de tablas y conservación de las fechas de entrevistas. Se inspeccionaron los nuevos controles en la sesión real conectada y capturas sintéticas de la agenda y modal. La creación, modificación y cancelación de eventos con los nuevos detalles se comprueban con un transporte controlado; no se escribieron citas de prueba en el calendario personal. Informes privados: `.local/interview-backend-regression.log`, `.local/interview-ui-final.log`, `.local/interview-ui-confirmation.log`, `.local/interview-migration-verification.json` y `.local/interview-review/`.

### Primera entrega de la bandeja y el proceso activo

Empresa → Postulaciones separa Por revisar, Proceso activo, Entrevistas y Finalizados. Las listas se paginan en el servidor, con búsqueda, orden estable por compatibilidad o fecha y filtros explícitos: sin revisar, compatibilidad ≥ 85 % y sin cálculo. El tablero activo carga ocho candidaturas por columna y permite pedir más. No mezcla las nuevas con quienes avanzaron. Conserva las etapas configurables y ofrece una lista alternativa. Las estadísticas y conteos se calculan en el servidor, sin derivarlos de la página visible.

El perfil y las respuestas se consultan sin abandonar la lista. En móvil el detalle reemplaza visualmente la bandeja y conserva su desplazamiento al regresar. Flechas navegan; A avanza a la etapa elegida y R abre el motivo y el mensaje de finalización. Los atajos no actúan al escribir ni sobre modales. Avances, valoraciones y movimientos se guardan directamente con control de versión; los errores mantienen la candidatura y el formulario. Se confirma la contratación por separado. No hay descarte automático por puntuación.

La migración `0049_application_review` añade la fecha de revisión individual y su índice. Ya no se llama al marcado masivo de vistas al abrir la vacante. La revisión no cambia la etapa ni envía un aviso de avance. No se infieren revisiones reales a partir del estado histórico «seen», que antes podía proceder del marcado masivo. Las puntuaciones se leen de recomendaciones persistidas mediante una consulta conjunta; los cálculos que faltan se solicitan solo para el perfil seleccionado. La autorización y el acceso al perfil evitan cargar todas las vacantes y postulaciones de la empresa. La respuesta de lista excluye CV, respuestas libres y notas privadas; el detalle comprueba la pertenencia a la vacante. Los entrevistadores conservan únicamente su acceso a procesos asignados.

Se reemplaza la página monolítica por componentes de bandeja, perfil, tablero y decisiones. Se retiran controles de pendientes y estilos del tablero anterior que quedaron sin uso. Antes de migrar se verificó un respaldo de la base local; después se compararon recuentos y el contenido existente de las postulaciones, además de comprobar integridad SQLite. No se modificaron etapas, fechas ni documentos existentes como parte de la migración.

Validación: 73 pruebas backend de API, migraciones, organizaciones, postulaciones, entrevistas y una muestra sintética de 400 candidaturas. La prueba de volumen verifica páginas acotadas, ausencia de duplicados entre páginas, filtros, pertenencia y un número constante de consultas sin cargar las relaciones completas. Otra suite de acceso, perfiles, recorridos entre empresas y control de datos aprobó 20 pruebas, incluidas dos repeticiones de las nuevas comprobaciones. También pasan 220 pruebas frontend y nueve recorridos de interfaz de entrevistas y selección, con ambos temas y móvil/escritorio. Estos últimos cubren errores al guardar, feedback antes de notificar, teclado, cambio de vistas, arrastre después de registrar una revisión y recuperación de una consulta de vacantes fallida. Ruff, ESLint y compilación aprobados. Informes y capturas privados: `.local/recruitment-backend-tests.log`, `.local/recruitment-backend-access-tests.log`, `.local/recruitment-ui-final.log`, `.local/recruitment-migration-verification.json` y `.local/recruitment-review/`.

Esta entrega cubre la bandeja y el proceso activo. Las entrevistas múltiples, las rúbricas por criterios y la reserva de horarios quedan para las siguientes fases. La pestaña de entrevistas reutiliza las citas actuales por vacante. La puntuación disponible no demuestra validez predictiva ni una evaluación del modelo con personas reales; no se ejecutaron comunicaciones ni decisiones de prueba sobre candidaturas personales para validar este flujo.


### Flujo de selección e entrevistas — 23/10/2026

Se alinearon estado y etapa en las acciones de contratación, finalización y programación. El tablero cuenta con filtro por etapa y confirmación de movimientos antes de guardar y notificar; las candidaturas finalizadas son de solo lectura también en la API.

La confirmación de entrevista realizada se registra en `interview_completed_at` (migración `0050_interview_completion`). La vista distingue programadas, por registrar asistencia y pendientes de respuesta. No se infiere asistencia por una fecha pasada. Se conserva la fecha original, se añade historial y aviso al candidato, y una reprogramación limpia la confirmación anterior.

Validación: 66 pruebas backend, incluida migración y entrega de calendario con proveedor simulado; 223 pruebas frontend; 13 recorridos de interfaz a 360/1280 px en claro/oscuro. Las capturas con 400 postulaciones usan datos sintéticos de Playwright, no una cuenta persistente. La migración local se aplicó con copia de seguridad e integridad verificada; conservó todos los datos previos de postulaciones. No se enviaron decisiones a candidatos reales ni se crearon eventos de Google para estas pruebas.

Continúan fuera de esta entrega las entrevistas múltiples por postulación, reservas de disponibilidad y evaluaciones por criterios. El flujo actual gestiona una entrevista por candidatura con su historial de reprogramaciones.


### Seguimiento de plazos sin descarte automático — 23/10/2026

Se sustituyó el cierre por vencimiento por avisos de respuesta atrasada y pausa tras tres días laborables desde el aviso. La etapa, la candidatura y el último mensaje empresarial se conservan. La pausa se consulta fuera del tablero activo y admite retomar mediante ampliación pública limitada, avance real o programación de entrevista. El resultado de selección sigue requiriendo comunicación explícita.

La migración `0051_response_followup` añade marcas de retraso, pausa, primer incumplimiento y contador de ampliaciones. No reclasifica cierres previos. El trabajador revalida la protección de entrevistas, usa actualizaciones condicionadas por versión para evitar duplicados y omite periodos de gracia aún vigentes para no bloquear lotes posteriores. La reputación incorpora el incumplimiento sin asignar un rechazo al candidato.

Los plazos nuevos cuentan lunes a viernes en Colombia, sin calendario de festivos. Las ampliaciones requieren versión vigente, permisos de gestión, motivo público de 20 a 500 caracteres, fecha posterior al compromiso y un máximo de siete días laborables adicionales. Se permite una por etapa. Notas, consultas y valoraciones no reinician el plazo. Las pruebas de ciclo y notificaciones usan bases descartables y proveedores simulados.

Verificación de esta entrega: 80 pruebas backend, 227 pruebas frontend y 17 recorridos de interfaz en claro/oscuro y móvil/escritorio. La migración local preservó todas las columnas previas de las postulaciones y pasó la comprobación de integridad. El servidor local tiene activo el ciclo de seguimiento; la cuenta de empresa de demostración pudo consultar las cinco secciones y su política de plazos. Las pruebas de ampliación y pausa se ejecutaron sobre datos sintéticos, sin modificar decisiones de candidaturas personales.
