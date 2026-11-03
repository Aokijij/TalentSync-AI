# Integraciones de producción

Revisión: **29 de octubre de 2026**, hora de Colombia. Entorno comprobado: `https://talentsync-ai.pages.dev`, API en AWS Ohio. Configurar una clave y comprobar una operación real son estados distintos.

## Resultado

| Integración | Estado observado | Alcance y límites |
| --- | --- | --- |
| Google: acceso y registro | Comprobado con la cuenta del titular | Retorno HTTPS, creación pendiente, confirmación de nombre/profesión y aceptación legal por el titular; nuevo inicio de sesión después de la pausa también correcto. |
| GitHub: inicio de sesión | Configurado; prueba pendiente por decisión del titular | Callback público guardado. Para vincularlo a la cuenta creada con Google, la implementación actual exige confirmar una contraseña de TalentSync. Debe establecerla el titular con Recuperar acceso. No vincular directamente en la base de datos ni omitir esta validación. |
| Google Calendar | Conectado y comprobado | Renovación del permiso y creación, modificación y retirada de un único evento privado autorizado. Se comprobaron modalidad, dirección/enlace, duración y recordatorio. Sin invitados ni notas internas; el evento de prueba se retiró. |
| Gmail transaccional | Autorización renovada desde AWS y envío aceptado registrado | Solo envío desde el buzón del proyecto; no se concedió lectura de buzones. La aceptación no acredita recepción o lectura. No se enviaron mensajes sintéticos adicionales durante esta revisión. |
| Neon | Disponible desde el servidor y desde `/health/ready` | Esquema `0054_external_job_freshness`. Los consentimientos existentes se conservan; no se reemplazan sus versiones históricas. |
| R2 privado | Disponible desde AWS | Acceso autenticado del backend; archivos fuera del acceso público. |
| Microsoft Learn | Habilitado y comprobado | 20 recursos devueltos y paginación disponible. Credenciales Entra de la aplicación solo en servidor; consulta editorial, sin importar cursos automáticamente durante la prueba. |
| YouTube Data API v3 | Habilitada y comprobada | Lista pública consultada con una muestra de 12 vídeos. Dos solicitudes por consulta; presupuesto de consultas existente conservado. No descarga vídeos ni registra cursos sin revisión editorial. |
| GitHub: proyectos públicos | Habilitado y comprobado | Se revisó un repositorio público de referencia de 46 archivos. No se clona ni ejecuta código, no se consultan repositorios privados ni se añaden evidencias ajenas a un perfil. Es independiente del inicio de sesión con GitHub. |
| Codewars | Habilitado y comprobado | Respuesta pública de referencia con 13 señales de lenguajes. No se guardó en la cuenta del titular ni se presenta como certificación. |
| SENA | Consulta comprobada | Cuatro resultados públicos para Excel; se respetan robots, límites de tamaño/tiempo y revisión editorial. |
| Sapiencia | Consulta comprobada | Cinco convocatorias públicas devueltas. No se activó actualización periódica ni se importaron automáticamente. |
| Greenhouse | Habilitado y comprobado desde AWS | Portal público de referencia: 10 anuncios, tres con Colombia en su ubicación; un ID confirmado por la API original. No se importaron ofertas durante la prueba. |
| Lever | Habilitado y comprobado desde AWS | Portal público de referencia: 70 anuncios, uno con Colombia en su ubicación; un ID confirmado por la API original. No se importaron ofertas durante la prueba. |
| CV y compatibilidad | Comprobados al desplegar | Modelos offline en CPU, OCR separado de la exportación PDF. Los CV no se transmiten a Unstract ni a un proveedor nuevo de IA. |

La revisión final comprobó además un PDF sintético de dos páginas (texto y una imagen escaneada): detectó la página sin capa de texto y recuperó su formación con el trabajador OCR y las rutas de modelos del servicio. No se usaron documentos personales. Pasaron 100 pruebas críticas y diez comprobaciones adicionales de lectura/importación; ESLint, comprobaciones del proxy, compilación y revisión visual del nuevo flujo también correctas.

YouTube, Microsoft Learn, GitHub público y Codewars estaban habilitados en el entorno de trabajo, pero faltaban en la configuración de AWS. Se trasladaron solo sus claves y opciones ya existentes, se validaron y se reinició el servicio. Las credenciales siguen fuera de Git y del frontend. Las consultas exitosas de fuentes educativas quedaron registradas para el panel de integraciones.

El panel ahora registra también el intercambio de identidad por proveedor, conexión/sincronización de Calendar, aceptación del transporte de correo, proyectos públicos de GitHub y Codewars. Recupera fechas agregadas de operaciones anteriores sin devolver identidades, destinatarios o cuerpos de mensajes. Google y GitHub se muestran por separado para no dar por comprobados ambos al probar solo uno. Las renovaciones de autorización se identifican como tales; no se presentan como entrega de un correo o sincronización de una entrevista. «Disponible en la plataforma» reemplaza la etiqueta confusa «Disponible localmente». El SSO y los agregadores no activados se presentan como opcionales.

Se añadieron fuentes públicas por empresa en Greenhouse y Lever, sin claves nuevas, y un trabajador de vigencia para ofertas externas. Solo se muestran las confirmadas recientemente; consultar un enlace HTTP no basta. Véase [EXTERNAL_VACANCIES.md](EXTERNAL_VACANCIES.md).

## Pendientes que deben distinguirse

1. **Verificación externa de Google.** Calendar funciona para la cuenta autorizada, pero Google sigue mostrando «app no verificada». El 29 de octubre, la comprobación de marca rechazó la propiedad de la página principal aunque Search Console muestra al mismo titular como propietario verificado de esa URL desde el 27 de octubre. Se preparó el motivo de apelación, sin enviarlo: el formulario también exige justificación de permisos y un video de demostración de todos los clientes OAuth. El botón final permanece deshabilitado. Estar en modo Producción no significa tener aprobada la marca y los permisos sensibles. Véase el [expediente preparado](GOOGLE_OAUTH_VERIFICATION.md).
2. **Prueba real del inicio con GitHub.** El titular decidió dejarla pendiente. El análisis público de repositorios sí funciona; no demuestra que se haya completado el acceso OAuth.
3. **Vacantes externas automáticas.** JSearch, Jooble y Adzuna no tienen claves en producción. Permanecen desactivados. Las vacantes publicadas por empresas y la importación manual son independientes. No inventar vacantes ni activar sondeos para ocultar un catálogo vacío.
4. **SSO administrativo.** Workspace/Entra SSO no están configurados y no son requisitos del acceso actual mediante contraseña y MFA. Las credenciales Microsoft Learn no habilitan SSO. LinkedIn permanece retirado de la interfaz.

SMTP y Resend no son pendientes mientras Gmail sea el transporte elegido. No activar varios transportes. Certificados y verificación empresarial conservan su revisión manual; no hay una conexión a registros oficiales ni autenticación automática de documentos que deba anunciarse como disponible.

## Evidencia y mantenimiento

Los informes privados de la revisión están en `.local/` y `/var/lib/talentsync/`; no incluyen tokens en sus salidas. El evento temporal de Calendar tiene un identificador único y un resultado de limpieza confirmado. No se añadieron empresas, vacantes o entrevistas ficticias a producción para realizar la prueba.

La política de privacidad publicada se actualizó a `2026-10-29.1` para identificar a AWS como encargado de infraestructura y el procesamiento en Ohio. Se archivó el texto anterior y no se cambiaron las versiones aceptadas previamente por los usuarios. Los términos conservan la versión `2026-10-27.1`.

Tras cambiar una credencial, verificar desde AWS la operación mínima correspondiente. Un estado GET debe leer observaciones guardadas y no consumir cuotas. Mantener las actualizaciones automáticas de fuentes desactivadas hasta definir su presupuesto y vigencia. Revisar errores de autorización, cuotas y trabajadores; conservar mensajes de error sin respuestas privadas del proveedor.

Referencias: [verificación sensible de Google](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification), [requisitos del expediente](https://support.google.com/cloud/answer/13464321), [Microsoft Learn: autenticación y paginación](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-get-started).

## Comprobación periódica

`INTEGRATION_HEALTH_CHECKS_ENABLED=true` ejecuta comprobaciones cada seis horas: renovación de autorización de Gmail y Calendar, metadatos públicos de acceso social y una consulta de bajo coste a YouTube. No envía mensajes ni crea entrevistas. El panel distingue conectividad de una operación autorizada real y conserva ambas fechas. Las fuentes de empleo y formación usan sus propias tareas de actualización. `PUBLIC_LEARNING_REFRESH_ENABLED=true` actualiza Sapiencia y SENA cada día; el fallo de una fuente no bloquea la otra. Sapiencia conserva los estados abiertos y cerrados publicados oficialmente.
