# Revisión de estabilidad y listados

22 de octubre de 2026. Alcance: versión local, pruebas con datos ficticios y bases aisladas. Los resultados de cada ejecución se registran en `.local/verification/platform-review.json`; no se publican credenciales ni datos de cuentas.

## Cambios revisados

- **Vacantes:** mínimo seleccionable desde 40%, normalización de enlaces antiguos y de números de página inválidos. El filtro conserva la página solicitada durante la carga y ajusta el rango cuando llegan los resultados. Si falla la compatibilidad, explorar ofertas sin aplicar ese filtro requiere una acción explícita y muestra un aviso.
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

## Límites de la revisión

- La ejecución visual cubre componentes y sus interacciones con datos de prueba. No equivale a una revisión completa de cada pantalla autenticada ni establece comparaciones automáticas contra capturas de referencia aprobadas. La inspección manual se realizó sobre una selección representativa de las capturas.
- Correo externo, OAuth/SSO, calendarios sincronizados y otros proveedores requieren cuentas y configuración autorizadas. Las pruebas de adaptadores o transportes locales no equivalen a comprobar una entrega o conexión externa real.
- Las pruebas de concurrencia usan datos sintéticos. No representan una certificación de capacidad o una auditoría de producción.
- No se publicaron cambios ni se alteraron cuentas personales para realizar esta revisión.
