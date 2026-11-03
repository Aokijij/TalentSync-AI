# Correo transaccional de TalentSync

La aplicación comparte una plantilla HTML y una versión de texto entre SMTP,
Resend y Gmail autorizado. Incluye confirmación de correo, recuperación de acceso, cambio de correo
e invitaciones al equipo. No envía campañas ni transforma las notificaciones de
procesos en correos automáticamente.

## Diseño y recorrido

- Identidad TalentSync, una acción principal y enlace alternativo para copiar.
- Los enlaces de cuenta duran 30 minutos y se usan una sola vez; las invitaciones
  duran 3 días. Solo los enlaces del `PUBLIC_APP_URL` configurado generan botones.
- El usuario confirma desde la web; abrir el correo no ejecuta cambios.
- Recuperación responde igual para direcciones registradas y desconocidas.
- La interfaz indica revisar la bandeja de entrada y Spam. Una solicitud aceptada
  no es una garantía de entrega; el panel de operaciones distingue cola, aceptación,
  entrega y rebotes según la información disponible del proveedor.
- La compilación de producción excluye la ruta y las ayudas de la bandeja de
  desarrollo, incluso si recibe por error `local_mail: true`.

## Activación al desplegar

1. Configurar `PUBLIC_APP_URL` con el origen HTTPS definitivo. Los enlaces de los
   correos se construyen desde ese valor, nunca desde la URL de la petición.
2. Desactivar `LOCAL_MAIL_ENABLED`, `LOCAL_ADMIN_REVIEW_ENABLED` y
   `LOCAL_MFA_REVIEW_ENABLED`. Mantener los controles de producción existentes.
3. Seleccionar **un solo transporte**, SMTP, Resend o Gmail, y guardar sus credenciales
   exclusivamente como secretos del backend. No usar variables `VITE_*`.
4. Con Resend, verificar un dominio propio y configurar `RESEND_ENABLED`,
   `RESEND_API_KEY`, `RESEND_FROM` y `RESEND_WEBHOOK_SECRET`. Registrar el webhook
   de entrega conforme al adaptador existente. Con SMTP, configurar `SMTP_ENABLED`,
   `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`, `SMTP_USERNAME`, `SMTP_PASSWORD` y
   `SMTP_FROM`; usar TLS y un remitente permitido por el proveedor.
5. Comprobar con un destinatario autorizado: recepción en buzón real, enlaces HTTPS,
   un solo uso, caducidad, reintentos y el estado de entrega que ofrezca el transporte.

Crear una cuenta Gmail no activa el envío. No utilizar su contraseña normal como
contraseña SMTP. Mientras no se configure un transporte válido, las operaciones
que requieren correo devuelven un error y la interfaz permite volver a intentarlo.

## Gmail autorizado sin contraseña de aplicación

Usar un cliente OAuth de escritorio dedicado a la configuración del buzón del
proyecto. No reutilizar la autorización de Google Calendar ni las sesiones sociales.
Este cliente se usa una vez en el equipo del operador para obtener la autorización;
el servidor desplegado solo renueva el acceso desde sus secretos privados.

1. Habilitar Gmail API en el proyecto Google Cloud y crear un cliente OAuth de
   escritorio. Guardar su JSON en `.local/gmail-oauth-client.json`, nunca en Git.
2. Ejecutar con el Python del backend:
   `python scripts/gmail_authorize.py --sender DIRECCION_DEL_PROYECTO`.
   Abrir la URL loopback que indique el proceso y seleccionar el buzón del proyecto.
3. Conceder únicamente `gmail.send` y la identidad básica necesaria para comprobar
   el remitente. No se solicita leer, listar ni modificar los mensajes del buzón.
   El flujo valida estado, PKCE, cuenta esperada y permisos; no guarda autorizaciones
   de otra cuenta ni permisos más amplios. No crea mensajes en la base de datos.
4. Inyectar los valores de `.local/gmail-production.env` como secretos del backend:
   `GMAIL_MAIL_ENABLED`, `GMAIL_MAIL_CLIENT_ID`, `GMAIL_MAIL_CLIENT_SECRET`,
   `GMAIL_MAIL_REFRESH_TOKEN` y `GMAIL_MAIL_SENDER`. Los demás transportes deben
   permanecer desactivados. Las pruebas automatizadas no los heredan. Para
   comprobar el envío real en el entorno de trabajo, indicar expresamente
   `INTEGRATION_MAIL_TRANSPORT=gmail` en `.local/integrations.env` e incluir las
   cuatro credenciales `GMAIL_MAIL_*`. Los mensajes históricos con estado `local`
   no pasan a la cola real; revisar que no haya envíos pendientes antes de activar.
5. Revisar el estado de publicación OAuth antes de producción: en modo Prueba,
   Google puede caducar la autorización a los siete días. Registrar cualquier fecha
   de expiración informada y completar los requisitos de publicación/verificación
   aplicables antes de considerar estable la conexión.

Gmail conserva sus límites de envío; este transporte sirve para el arranque con
poco volumen. No confirma la recepción ni lectura. Ante un timeout ambiguo durante
el envío no se reintenta automáticamente para evitar duplicados: revisar el buzón
del remitente y solicitar un enlace nuevo si hace falta. Los errores de renovación
anteriores al envío sí pueden reintentarse sin duplicar mensajes.

No publicar credenciales, cuerpos de mensajes ni enlaces con tokens en capturas,
logs o repositorios. Las previsualizaciones deben usar datos y tokens sintéticos.

## Estado comprobado el 27 de octubre de 2026

La cuenta del proyecto `talentsyncadmin@gmail.com` tiene una autorización de solo
envío renovada después de pasar el consentimiento OAuth a producción. Se comprobó
la renovación del acceso y la identidad del remitente sin enviar otro correo ni
leer el buzón. Google no informó una expiración de siete días; la autorización
sigue siendo revocable y está sujeta a sus políticas. La configuración privada se
actualizó y el servidor de desarrollo se reinició con comprobaciones de salud.

Actualización del 29 de octubre: el backend de AWS renueva correctamente el permiso
y la base de producción registra un mensaje aceptado por el transporte. La cola
no muestra mensajes fallidos. No se enviaron nuevos mensajes sintéticos durante
la revisión de integraciones; no se confunde aceptación con recepción o lectura.

Search Console verificó el sitio público. La revisión de marca y permisos sensibles
de Google continúa pendiente de preparación/presentación; no confundir OAuth
«En producción» con una aplicación verificada ni con el backend desplegado.
