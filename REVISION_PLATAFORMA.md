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

- Se comprobaron las rutas principales con cuentas de demostración y una selección representativa de capturas. No hay comparaciones automáticas contra imágenes aprobadas. Los recorridos no cubren todas las combinaciones posibles de datos, permisos de miembros de equipo, dispositivos o navegadores.
- Correo externo, OAuth/SSO, calendarios sincronizados y otros proveedores requieren cuentas y configuración autorizadas. Las pruebas de adaptadores o transportes locales no equivalen a comprobar una entrega o conexión externa real.
- Las pruebas de concurrencia usan datos sintéticos. No representan una certificación de capacidad o una auditoría de producción.
- No se publicaron cambios ni se alteraron cuentas personales para realizar esta revisión.
