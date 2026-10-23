# Entrega de correo, calendario y control de datos

## Qué está implementado y qué requiere proveedor

La plataforma tiene webhook firmado de Resend, sincronización delegada con Google Calendar, exportación y eliminación de datos propios, reintentos de limpieza y diagnósticos operativos. La configuración y las pruebas simuladas no prueban entrega externa ni autorización real de Google. Mantener esas integraciones como pendientes hasta comprobarlas con cuentas autorizadas. Outlook queda fuera de esta entrega: se priorizó Google Calendar.

## Google Calendar

Crear un cliente OAuth web en Google Cloud, habilitar Calendar API y registrar exactamente `https://TU-DOMINIO/api/v1/account/calendar/google/callback`. Para desarrollo local con Vite, su proxy `/api` debe llegar al backend. Usar el dominio público de la plataforma en `PUBLIC_APP_URL`, sesión por cookies activa y estos valores privados en el gestor de secretos:

```dotenv
CALENDAR_SYNC_ENABLED=true
CALENDAR_GOOGLE_CLIENT_ID=
CALENDAR_GOOGLE_CLIENT_SECRET=
```

No reutilizar silenciosamente el consentimiento de iniciar sesión con Google. Cada persona entra en Seguridad → Calendario, autoriza el alcance `calendar.events.owned` y elige una entrevista desde su proceso. El consentimiento offline y PKCE se vinculan al usuario, sesión y navegador; el estado vence en diez minutos y no se reutiliza. El token de renovación se cifra con la clave de la instalación, nunca se entrega al navegador ni se exporta.

La plataforma crea un evento privado en el calendario principal propio: cargo, enlace al proceso, fecha, duración elegida y aviso de 30 minutos. No añade invitados, respuestas, notas ni puntuaciones. Duración predeterminada de la copia: 45 minutos; el usuario debe acordar la duración real con la empresa. Un identificador estable evita duplicar eventos ante reintentos. El trabajador revisa cada 30 segundos las entrevistas elegidas: cambio de fecha/versión actualiza, finalización/cancelación elimina el evento. Fallos transitorios tienen hasta cinco intentos; revocación exige nueva autorización. Cambios manuales o eliminación del evento en Google pueden requerir volver a sincronizar; no hay sincronización de Google hacia TalentSync.

Desconectar elimina el token y detiene sincronizaciones; los eventos ya copiados permanecen en Google y se pueden borrar allí. Eliminar la cuenta tampoco promete borrar copias externas. Si rota la clave de cifrado sin migrar tokens, será necesaria nueva autorización.

Verificación externa pendiente: consentimiento de una cuenta de prueba autorizada, crear, mover, cancelar, revocar y reconectar. Revisar la pantalla de consentimiento y los requisitos de publicación/verificación que Google indique para el proyecto. [Documentación OAuth de Google](https://developers.google.com/identity/protocols/oauth2/web-server), [creación de eventos](https://developers.google.com/workspace/calendar/api/guides/create-events).

## Correo y confirmación de entrega

Configurar Resend como antes y añadir `RESEND_WEBHOOK_SECRET` (secreto de firma del endpoint). Endpoint público: `POST /api/v1/webhooks/resend`. Suscribir eventos `email.sent`, `email.delivered`, `email.delivery_delayed`, `email.bounced`, `email.complained` y `email.failed`. No desactivar autenticación de otras rutas. El webhook valida el cuerpo original, firma Svix, identificador y ventana de cinco minutos; limita el cuerpo a 64 KB y deduplica identificadores firmados.

La cola distingue envío al transporte de entrega: un 2xx de Resend registra el ID del proveedor y estado aceptado. Solo un evento válido declara entregado, rebotado, retrasado o fallido. Eventos anticipados se reconcilian al guardar el ID del envío y los atrasados no revierten la entrega. SMTP confirma aceptación por su transporte, no entrega ni lectura. No se añade seguimiento de apertura.

Administración → Motor e integraciones → Operación y correos muestra estados, intentos e ID interno, sin destinatarios, cuerpos ni credenciales. Verificar con un destinatario de prueba autorizado y eventos de prueba del proveedor; no enviar correos a usuarios para validar. [Verificación de webhooks Resend](https://resend.com/docs/webhooks/verify-webhooks-requests).

## Portabilidad y eliminación

Seguridad → Mis datos permite descargar ZIP o eliminar la cuenta. Ambas acciones requieren contraseña actual y segundo factor si está activo, además de CSRF con sesiones de navegador. Usuarios sociales sin contraseña deben usar Recuperar acceso. La copia reúne JSON propio, borradores, postulaciones (sin notas ni valoraciones privadas de empresas), prácticas, CV PDF guardados y originales/fotos disponibles. Excluye hashes de contraseña, claves MFA, tokens, sesiones y credenciales sociales/calendario. El manifiesto indica archivos incluidos y si hay original de CV disponible. Límite de copia: 50 MB; si faltan permisos de almacenamiento o se supera, se informa y no se descarga una copia incompleta silenciosamente.

Eliminar exige escribir ELIMINAR y una confirmación adicional. Retira perfil, procesos personales y documentos asociados, sesiones, tokens, datos de aprendizaje, evidencias y señales de personalización; invalida artefactos experimentales que las usaban. Elimina informes vinculados a la postulación retirada, anonimiza autoría de auditorías del modelo y conserva registros empresariales ajenos. Una cuenta propietaria de empresa debe transferir propiedad con administración antes de eliminarse; debe quedar otra cuenta administradora. No se borran la organización ni procesos de otras personas.

La retirada de registros se confirma antes de limpiar archivos. Una tarea persistente reintenta archivos privados fallidos; el comprobante informa si esa limpieza sigue pendiente. Completada, la tarea deja de conservar el ID del usuario. El trabajador de limpieza se activa con `ACCOUNT_CLEANUP_ENABLED=true` (valor predeterminado) y revisa cada minuto. Sus errores son genéricos; Administración puede ver la cantidad pendiente. Un despliegue con varios procesos comparte arrendamientos para impedir limpiar a la vez la misma tarea.

Conservación automática opcional: `ACCOUNT_RETENTION_ENABLED=true`, `ACCOUNT_RETENTION_DAYS=90` (7–365). Retira tokens/estados OAuth/sesiones/correos vencidos y comprobantes anónimos completados tras ese plazo; nunca descarta tareas de limpieza pendientes por antigüedad. Los eventos de entrega tienen además `MAIL_EVENT_RETENTION_DAYS=90` cuando llegan eventos. Aprobar y comunicar los plazos antes de producción. No equivale a una evaluación legal ni elimina copias que empresas ya hayan descargado. Las copias de seguridad deben expirar con una política aprobada y los borrados deben reaplicarse antes de reabrir una restauración; no devolver una copia antigua directamente a servicio.

## Disponibilidad, métricas y recuperación

`/health` conserva compatibilidad; `/health/live` comprueba proceso; `/health/ready` devuelve 200 si base de datos y almacén privado responden, 503 en otro caso. El endpoint no expone direcciones ni excepciones. Readiness comprueba disponibilidad de lectura, no prueba todos los permisos de escritura ni proveedores externos. Utilizarlo como sonda de readiness del servicio, liveness para reinicio. Desplegar migraciones antes de arrancar los trabajadores.

Las respuestas incluyen ID de solicitud y Server-Timing. El panel operativo muestra hasta 512 muestras por ruta parametrizada, en 15 minutos y por proceso: p95, 5xx y colas. No almacena cuerpos, cabeceras, correos ni IDs de usuario en métricas. Alerta sobre dependencias, tareas fallidas, limpieza pendiente, conservación desactivada y rutas con p95 > 2 s o más de 5 % de 5xx con al menos 20 muestras. Complementarlo en producción con monitor externo, agregación entre instancias, disponibilidad histórica y alertas a responsables; no se ha conectado un servicio externo de monitorización.

Desde la raíz, con backend local levantado:

```powershell
backend/.venv/Scripts/python.exe scripts/operations_check.py probe --output .local/operations/probe.json
backend/.venv/Scripts/python.exe scripts/operations_check.py load --requests 40 --workers 4 --output .local/operations/load.json
backend/.venv/Scripts/python.exe scripts/operations_check.py recovery --output .local/operations/files-recovery.json
backend/.venv/Scripts/python.exe scripts/staging_postgres.py check
```

Las solicitudes de carga solo alcanzan readiness; no prueban carga de CV, matching o vídeo. Máximo 200 solicitudes y 8 conexiones. Destino predeterminado: loopback; para staging se requiere HTTPS y `--staging-host` con el nombre autorizado. No apuntar a producción como ensayo. La recuperación de archivos usa documentos sintéticos y compara hashes; el ensayo PostgreSQL aplica migraciones, prueba flujos y carrera de cola, realiza pg_dump/pg_restore y compara todas las filas en bases exclusivas del ensayo. No es una restauración de Azure.

Antes de publicar: ejecutar pruebas y migraciones en staging, respaldar base y archivos privados de forma coherente, comprobar restauración en aislamiento, registrar RPO/RTO medidos, revisar HTTPS/cookies/MFA/secretos/permisos de almacenamiento, activar conservación aprobada, probar entrega y Calendar con cuentas autorizadas y completar el piloto según [protocolo](PROTOCOLO_PILOTO.md). La publicación y configuración de servicios externos siguen pendientes; no se ejecutan con estas herramientas.
