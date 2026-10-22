# Revisión del producto y las integraciones

Revisión del 21 de octubre de 2026. Alcance: código actual de la rama local, pruebas y configuración local reducida a indicadores booleanos. No se consultaron cuentas externas, no se enviaron correos, no se verificó producción y no se activó infraestructura. Las prioridades son una propuesta de trabajo; no representan funcionalidades implementadas en esta revisión.

## Qué mejoraría primero

| Prioridad | Mejora | Evidencia y motivo | Criterio de cierre |
| --- | --- | --- | --- |
| 1 | Estabilidad visual y accesibilidad | El CI ejecuta pruebas de lógica/SSR, lint y compilación; no incorpora una suite de comparaciones visuales. Los fallos recientes de ancho/alineación pasan esas comprobaciones. Hay reglas compartidas y repetidas en `frontend/src/styles/index.css` y hojas de perfil. | Componentes comunes para tarjetas, pies, filtros, cabeceras y estados; revisión de contraste/foco/teclado; capturas de referencia a 360, 768, 1280 y 1440 px, con textos largos y estados vacíos/cargando/error, en los temas de cada rol. |
| 2 | Piloto completo en un entorno equivalente a producción | Hay CI, guiones de PostgreSQL, migraciones y restauración locales. Su existencia no demuestra un despliegue operativo actual. La preparación de staging requiere presupuesto y separa correctamente sus recursos. | Un recorrido candidato → empresa → administrador sobre HTTPS y PostgreSQL, fotos/CV privados, sesión/CSRF, tareas programadas y restauración real; carga HTTP concurrente y p95 por operación. |
| 3 | Observabilidad de la aplicación | Se encontraron `/health`, `Server-Timing`, logs y una plantilla de Log Analytics. No se encontró instrumentación de trazas/métricas de aplicación ni alertas operativas en el código revisado. `/health` devuelve un estado fijo. | Distinguir liveness/readiness, comprobar dependencias, identificar solicitudes, medir colas/proveedores/modelo y alertar fallos o latencias sin registrar CV, identificaciones ni tokens. |
| 4 | Gobierno de datos personales | Hay preferencias, consentimiento para personalización y controles de visibilidad. No se encontró un recorrido completo de exportación de datos de cuenta, supresión de cuenta y conservación automatizada; exportar el CV cubre otro propósito. | Exportación y eliminación coherentes entre base, archivos y datos derivados; excepciones y plazos definidos, reautenticación, registro de decisiones y pruebas de autorización. |
| 5 | Estado único de integraciones y documentación | Los documentos antiguos contienen funciones retiradas y estados que ya cambiaron. El panel de disponibilidad todavía enumera GitHub/Codewars aunque se retiraron del recorrido principal y no refleja todas las fuentes educativas recientes. | Un inventario común con estados separados: implementado, habilitado, última comprobación correcta y fallo actual; rutas/interfaz/documentación consistentes. |
| 6 | Medir utilidad con usuarios reales | Existen compatibilidad, brechas, auditorías y contadores. Falta validar su utilidad con una muestra real consentida y evaluar el recorrido completo, además de los escenarios sintéticos. | Medir postulaciones relevantes, avance a entrevista, tiempos de respuesta, abandono y aprendizaje útil; revisar recomendaciones por ocupación y región. |

Las comparaciones visuales pueden incorporarse al CI con [Playwright](https://playwright.dev/docs/test-snapshots). Es una propuesta para la siguiente etapa, no una ejecución de navegador durante esta revisión. [OpenTelemetry para Python](https://opentelemetry.io/docs/languages/python/) permite instrumentar las señales operativas; el backend actual no necesita cambiar de framework para ello.

## Integraciones: qué existe y qué falta

Los estados siguientes describen exclusivamente el entorno local inspeccionado. Habilitado/configurado no equivale a conexión comprobada ni a entrega exitosa.

| Integración | Estado encontrado | Siguiente trabajo útil |
| --- | --- | --- |
| YouTube | Adaptador, consulta editorial e importación implementados; habilitado en configuración local. | Consolidar estado/última comprobación, cuotas y tratamiento de recursos retirados. No necesita volver a implementarse ni mostrar instrucciones de activación cuando está configurado. |
| Microsoft Learn | Conector autenticado, vistas previas e importación implementados; habilitado en configuración local. | Comprobar el recorrido con la aplicación autorizada, metadatos y paginación; mantener la revisión de habilidades antes de publicar. |
| SENA y Sapiencia | Fuentes públicas, caché y actualización periódica de estados implementadas; actualización habilitada localmente. | Mostrar el resultado de cada actualización, recursos inaccesibles y antigüedad; ampliar cobertura útil por ciudad. El directorio de otras entidades es una referencia, no una sincronización de todas sus convocatorias. |
| Resultados y certificados de cursos | Registro por el candidato y evidencias declaradas; el catálogo de un proveedor no verifica que una persona terminó el curso. | Una integración de resultados/certificados requiere acceso autorizado al proveedor y comprobar identidad, titularidad, revocación y alcance. Mantener revisión manual donde no haya un contrato disponible. |
| Correo SMTP / Resend | Adaptadores, outbox, leases, reintentos e idempotencia implementados. El lanzador local fuerza buzón de desarrollo y desactiva entrega externa. La documentación registra un envío histórico de prueba de Resend. | Completar seguimiento de entrega/rebote y errores permanentes. El adaptador actual toma la aceptación HTTP como envío y no persiste un identificador del proveedor ni recibe sus eventos. |
| Google / GitHub / LinkedIn | Adaptadores sociales implementados; sin cliente y secreto configurados en este entorno local. | Elegir el primer proveedor según el público y probar login, vínculo con cuenta existente, revocación, permisos y recuperación. Evitar activar todos a la vez sin comprobar cada recorrido. |
| Workspace / Entra ID | SSO y aprovisionamiento implementados; sin credenciales locales. | Validar con una organización real antes de hacerlo obligatorio. Es una prioridad posterior si el piloto no requiere SSO corporativo. |
| Jooble / Adzuna / JSearch | Adaptadores de vacantes existentes; sin credenciales locales. La importación manual sigue disponible. | Seleccionar una fuente autorizada con cobertura adecuada para Colombia; comprobar vigencia, deduplicación, enlaces, licencias y bajas de vacantes. |
| Google Calendar / Outlook | Existen fechas de entrevistas en los procesos; no se encontró sincronización con calendarios externos ni exportación ICS. | Empezar por añadir al calendario; después crear, reprogramar y cancelar eventos con autorización, zona horaria y un identificador estable para evitar duplicados. |
| Verificación empresarial, académica y profesional | Revisión manual, soportes y comparación académica interna. La afinidad entre programas no autentica un diploma. | Definir qué se verifica y usar registros o proveedores autorizados donde exista acceso. Mostrar resultados verificables y su fecha; no presentar como verificado un dato declarado. |

Para el correo, los [webhooks de Resend](https://resend.com/docs/webhooks/introduction) permiten recibir eventos de entrega y rebote. Una implementación debe verificar la firma, deduplicar eventos y conservar la relación con el mensaje interno. No implica que el destinatario haya leído el correo.

Los calendarios tienen APIs oficiales para [Google Calendar](https://developers.google.com/workspace/calendar/api/guides/create-events) y [Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/user-post-events?view=graph-rest-1.0). La conexión al calendario es una autorización separada del acceso social. Las operaciones de agenda pueden enviar invitaciones; deberán formar parte de una acción explícita de la empresa.

## Orden de trabajo propuesto

1. Unificar los componentes visuales y añadir las comprobaciones de interfaz que hoy faltan.
2. Ejecutar un piloto completo con observabilidad, restauración y tratamiento de datos definidos.
3. Cerrar correo transaccional con estado de entrega y un acceso social real.
4. Añadir calendario y una fuente de vacantes autorizada según la necesidad del piloto.
5. Mejorar actualización del catálogo, cobertura geográfica y verificación de resultados/documentos mediante acuerdos disponibles.
6. Decidir nuevas funciones a partir del uso real. Más canales de mensajería, nuevos modelos y monetización quedan como decisiones posteriores a esa validación.

## Evidencias del repositorio

- Pruebas y construcción: `.github/workflows/ci.yml`, `frontend/tests/`, `frontend/package.json`.
- UI y reglas compartidas: `frontend/src/styles/index.css`, `frontend/src/styles/profile-page.css`, `frontend/src/styles/learning-discovery.css`.
- Configuración y diagnóstico: `scripts/local.py`, `backend/app/core/config.py`, `backend/app/domain/services/integration_readiness.py`, `backend/app/api/v1/routes/personalization.py`.
- Fuentes educativas: `backend/app/infrastructure/youtube_learning.py`, `backend/app/infrastructure/learn_catalog.py`, `backend/app/infrastructure/public_learning.py`, `backend/app/infrastructure/education_scheduler.py`, `backend/app/application/use_cases/learning_sources.py`.
- Correo: `backend/app/application/use_cases/mail_delivery.py`, `backend/app/infrastructure/security/resend.py`, `backend/app/infrastructure/mail_scheduler.py`.
- Sesión, privacidad y rutas: `backend/app/application/use_cases/account_security.py`, `backend/app/api/v1/routes/account.py`, `backend/app/api/v1/router.py`.
- Infraestructura y operación: `infra/staging/README.md`, `infra/staging/foundation.bicep`, `scripts/staging_postgres.py`.
- Alcance y estados históricos: `LOCAL_HANDOFF.md`, `docs/INTEGRACIONES_PRIMERA_ETAPA.md`. Para describir el estado actual se contrastaron con el código y los indicadores locales; no se tomaron como prueba de conexión vigente.
