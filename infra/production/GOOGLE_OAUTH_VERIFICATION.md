# Expediente de verificación de Google

Preparado el 29 de octubre de 2026. Proyecto: `talentsync-educacion`. Aplicación pública: https://talentsync-ai.pages.dev/.

## Estado real

El acceso con Google y la conexión de Calendar se comprobaron con el titular. El proyecto está en Producción, pero su marca y los permisos sensibles aún no están aprobados. No anunciar la aplicación como verificada.

La comprobación automática de marca dice que la página principal no pertenece al solicitante. Search Console muestra la propiedad de prefijo exacto `https://talentsync-ai.pages.dev/` como **Propietario verificado**, bajo la misma cuenta administradora del proyecto, añadida el 27 de octubre. Se volvió a comprobar el 29 de octubre, después de más de 24 horas. La etiqueta de verificación sigue presente y las páginas legales son públicas.

En «Ver problemas» se eligió «Considero que los problemas detectados son incorrectos». La pantalla siguiente exige además justificación de permisos y un enlace a un video de YouTube. **No se envió la solicitud**; el botón Confirmar permanece deshabilitado. No hay un plazo de aprobación iniciado.

## Texto preparado para la apelación

Motivo: **El hallazgo es incorrecto**.

> Google Search Console muestra la propiedad https://talentsync-ai.pages.dev/ como Propietario verificado en la misma cuenta de Google que administra el proyecto talentsync-educacion. La propiedad se añadió el 27 de octubre de 2026 y se comprobó de nuevo el 29 de octubre, transcurridas más de 24 horas. La página principal es pública, conserva la etiqueta de verificación y enlaza las páginas públicas de privacidad y términos. Solicitamos revisar el hallazgo automático de falta de propiedad.

Las capturas privadas de Search Console y del formulario están en `.local/google-search-console-verified.png` y `.local/google-verification-prepared.png`. No incluyen claves ni tokens. El texto introducido en el formulario no debe considerarse un borrador guardado en Google; se conserva aquí para recuperarlo.

## Justificación propuesta de los permisos sensibles

Texto para «¿Cómo se usarán los permisos?» (menos de 1000 caracteres):

> TalentSync usa calendar.events.owned para añadir al calendario principal del usuario las entrevistas que este elige y actualizar o retirar esos mismos eventos cuando se reprograman o cancelan. Incluye fecha, duración, modalidad, enlace o dirección y recordatorio; no añade invitados ni notas internas. Un permiso de solo lectura no permite mantener estos eventos y no necesitamos acceso a calendarios ajenos. Gmail.send se autoriza únicamente para el buzón operativo talentsyncadmin@gmail.com, mediante un cliente de escritorio dedicado, y permite enviar confirmaciones, recuperación de acceso, cambios de correo e invitaciones al equipo solicitadas en la plataforma. Los candidatos no conceden Gmail.send. No leemos ni listamos mensajes, no enviamos campañas y un permiso más limitado no permite el envío. Los tokens se conservan solo en el servidor; los permisos se pueden revocar en Google.

Esta justificación describe el código actual; no cambia permisos ni concede accesos nuevos. Los permisos básicos `openid`, `userinfo.email` y `userinfo.profile` identifican la cuenta del acceso social. No se solicita lectura de Gmail ni acceso a repositorios privados.

## Demostración que falta

Se requiere un video real, accesible al revisor, que muestre los clientes OAuth del proyecto. No sustituirlo por capturas animadas, resultados inventados o una URL de ejemplo.

1. Mostrar la página pública, privacidad y términos y la identidad de TalentSync.
2. Mostrar el inicio con Google, su consentimiento y el regreso a la plataforma. Al registrar una cuenta nueva, mostrar la confirmación de nombre/profesión y aceptación legal realizada por su titular.
3. Mostrar Seguridad → Calendario, la conexión opcional y la pantalla de consentimiento con `calendar.events.owned`. Mostrar el aviso de app no verificada si Google lo presenta.
4. En un entorno de prueba, añadir una entrevista autorizada, mostrar modalidad, enlace/dirección, duración y recordatorio; reprogramarla y cancelarla, mostrando los cambios del mismo evento. No grabar datos de candidatos reales ni crear postulaciones ficticias en producción. La prueba privada del 29 de octubre ya terminó y su evento se retiró; cualquier nueva prueba requiere definir su alcance.
5. Mostrar el cliente de correo y la autorización de solo envío del buzón operativo. El titular completa cualquier contraseña, verificación o consentimiento que aparezca. Mostrar una operación transaccional autorizada y su resultado sin exponer el enlace de recuperación, códigos, tokens o credenciales. El permiso de Gmail no debe aparecer en el consentimiento del candidato.
6. Mostrar la desconexión y explicar que los permisos también pueden revocarse en la Cuenta de Google.

No publicar contraseñas, códigos de autorización, tokens, enlaces de recuperación, archivos privados ni datos de terceros. Usar datos de prueba autorizados. La publicación del video y el envío final a revisión quedan pendientes; no se subió contenido ni se enviaron mensajes adicionales durante esta revisión.

## Para completar el envío

Con el video real aprobado y su enlace disponible, guardar la justificación y la URL en Acceso a los datos, recuperar el motivo de apelación, revisar el resumen y enviar. Si aparece una declaración contractual, debe aceptarla el titular. Confirmar en la consola el estado «en revisión» antes de informar que se presentó. La aprobación depende de Google y puede requerir información adicional.

Referencias: [verificación de permisos sensibles](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification), [requisitos del expediente](https://support.google.com/cloud/answer/13464321), [problemas de la página principal](https://support.google.com/cloud/answer/13807376?hl=es).
