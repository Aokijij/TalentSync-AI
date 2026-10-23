# Activar acceso social, Google Calendar y correo

## Estado actual

El servidor admite registro e inicio de sesión de candidatos con Google, GitHub y
LinkedIn, además de vincular y desvincular proveedores desde Seguridad. El registro
ahora muestra las mismas opciones habilitadas que el inicio de sesión. Las cuentas
de empresa conservan su registro y sus permisos propios.

Google y GitHub están configurados y habilitados para el registro e inicio de
sesión local. Google Calendar está habilitado con su cliente independiente.
LinkedIn sigue pendiente de credenciales y origen HTTPS. Se comprobaron los
botones contra la API real y la generación de enlaces de autorización; todavía
falta completar el consentimiento externo y comprobar los callbacks registrados
en cada consola. Disponer de configuración no demuestra un acceso externo completo.

Las credenciales están únicamente en `.local/integrations.env`, excluido de Git.
No copies ese archivo a documentación o repositorios. El correo externo sigue
desactivado. No se enviaron correos, se crearon cuentas externas ni se contrataron
servicios durante esta activación.

## Preparar la configuración privada

Desde la raíz del proyecto:

```powershell
backend/.venv/Scripts/python.exe -X utf8 scripts/local.py integrations --init
```

El comando crea el archivo si falta y conserva cualquier archivo existente. Ábrelo
en tu editor y escribe los valores allí, nunca en el chat ni en archivos versionados.
Formato: `CLAVE=valor`, sin comillas ni expansión de variables.

Cuando hayas configurado al menos un proveedor, cambia `INTEGRATIONS_ENABLED=true`.
Puedes activar un proveedor cada vez. Para consultar los callbacks y los estados:

```powershell
backend/.venv/Scripts/python.exe -X utf8 scripts/local.py integrations
```

El informe oculta claves, identificadores de cliente y remitentes; no envía mensajes
ni llama a proveedores. `configured` significa que hay configuración, no que se haya
completado un acceso externo.

Reinicia la API después de cambiar el archivo. Usa siempre el origen exacto de
`PUBLIC_APP_URL` en el navegador: `localhost` y `127.0.0.1` son orígenes distintos.
El frontend y `/api/v1` deben estar disponibles en ese mismo origen. Vite ya redirige
`/api` a la API local en el puerto 8000.

## Google: registro e inicio de sesión

1. En [Google Auth Platform](https://console.cloud.google.com/auth/overview), crea
   o selecciona un proyecto propio. Configura nombre de la aplicación, contactos
   y audiencia. En modo de prueba, agrega las cuentas que harán la comprobación.
2. Crea un cliente OAuth de tipo **Aplicación web**. Registra el origen usado por
   TalentSync y este URI de redirección para el entorno local actual:
   `http://127.0.0.1:5173/api/v1/auth/social/google/callback`.
3. Guarda el ID y el secreto en `OAUTH_GOOGLE_CLIENT_ID` y
   `OAUTH_GOOGLE_CLIENT_SECRET` del archivo privado.
4. Reinicia y comprueba que Google aparece en `/login` y `/registro`. El flujo
   solicita `openid email profile`; no solicita acceso al calendario.

Para publicar, registra también el callback del dominio HTTPS definitivo. No uses
un cliente de escritorio ni una clave de API en lugar del cliente OAuth web.
[Documentación oficial de Google](https://developers.google.com/identity/protocols/oauth2/web-server).

## GitHub: registro e inicio de sesión

1. Abre [Developer settings → OAuth Apps](https://github.com/settings/developers)
   y registra una OAuth App para TalentSync.
2. Usa `http://127.0.0.1:5173` como URL de inicio local y
   `http://127.0.0.1:5173/api/v1/auth/social/github/callback` como callback.
3. Guarda `OAUTH_GITHUB_CLIENT_ID` y `OAUTH_GITHUB_CLIENT_SECRET` en el archivo
   privado. Conviene separar las aplicaciones local y publicada.
4. Reinicia y prueba el consentimiento. Solo se solicitan `read:user user:email`;
   el acceso no autoriza repositorios privados. Se necesita un correo principal
   verificado en GitHub.

[Crear una OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).

## LinkedIn: registro e inicio de sesión

1. Crea tu aplicación en [LinkedIn Developers](https://www.linkedin.com/developers/apps).
   Completa los datos y verificaciones que solicite la consola para tu aplicación.
2. En **Products**, solicita **Sign In with LinkedIn using OpenID Connect**.
   Comprueba que se concedieron `openid`, `profile` y `email`.
3. En **Auth**, registra `https://TU-DOMINIO/api/v1/auth/social/linkedin/callback`.
   LinkedIn requiere callback HTTPS. El origen HTTP local actual no lo habilita.
4. Configura `OAUTH_LINKEDIN_CLIENT_ID` y `OAUTH_LINKEDIN_CLIENT_SECRET` en el
   entorno que sirve ese dominio. No pegues literalmente `TU-DOMINIO`.
5. Para probar en local necesitas un origen HTTPS loopback con certificado
   confiable y frontend/API juntos; cambiar solamente la URL del archivo no
   instala HTTPS. No publiques la base local personal mediante un túnel.

El arranque aislado `scripts/local.py` solo acepta orígenes loopback. En un
despliegue se configuran directamente las variables del backend y su origen
público HTTPS, con cookies seguras, hosts y CORS explícitos. No se creó un
despliegue ni un dominio como parte de esta preparación.

LinkedIn puede omitir el correo verificado; en ese caso TalentSync rechaza el
acceso y se puede usar el registro por correo. La conexión no acredita experiencia
ni valida la identidad profesional.
[Producto OpenID Connect](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2)
y [configuración del callback](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow).

## Google Calendar: consentimiento independiente

1. Habilita **Google Calendar API** en tu proyecto Google. Prepara un cliente
   OAuth web para Calendar; se recomienda separarlo del cliente de acceso.
2. Registra este callback local exacto:
   `http://127.0.0.1:5173/api/v1/account/calendar/google/callback`.
3. Completa `CALENDAR_GOOGLE_CLIENT_ID`, `CALENDAR_GOOGLE_CLIENT_SECRET` y
   `CALENDAR_SYNC_ENABLED=true` en el archivo privado. Agrega las cuentas de
   prueba a la audiencia si el proyecto está en modo de prueba.
4. Reinicia. En Seguridad autoriza Calendar y luego sincroniza una entrevista
   propia. El permiso es `https://www.googleapis.com/auth/calendar.events.owned`.
   Entrar con Google no concede este permiso automáticamente.
5. Comprueba en el calendario la creación, una reprogramación y la cancelación
   de una entrevista de prueba. Desconecta desde Seguridad y confirma que se
   detienen las sincronizaciones. Los eventos ya copiados se conservan al desconectar.

Los consentimientos externos, las restricciones del modo de prueba y una eventual
verificación de Google se gestionan en su consola. No debe confundirse disponer
de credenciales con tener autorización de todas las cuentas.
[Crear eventos en Google Calendar](https://developers.google.com/workspace/calendar/api/guides/create-events).

## Correo de cuentas y confirmación de entrega

Elige un único transporte mediante `INTEGRATION_MAIL_TRANSPORT`:

- `local`: continúa la bandeja de desarrollo. No manda correo externo.
- `resend`: completa `RESEND_API_KEY` y `RESEND_FROM` con un remitente de tu
  dominio verificado en Resend. El remitente `onboarding@resend.dev` sirve para
  la prueba aislada autorizada, no para abrir registro a cualquier persona.
- `smtp`: completa servidor, puerto, seguridad, remitente y, si corresponde,
  usuario/contraseña SMTP. No combines SMTP y Resend.

Los mensajes que ya están marcados `local` se conservan así: no se convierten en
envíos pendientes. Los nuevos mensajes de verificación y recuperación usan el
transporte seleccionado. No reetiquetes ni reenvíes en bloque mensajes de datos
de demostración.

Para confirmar entrega/rebote en Resend, registra un webhook público HTTPS en
`/api/v1/webhooks/resend` y guarda su secreto de firma en
`RESEND_WEBHOOK_SECRET`. Usa las notificaciones de entrega, rebote y queja
admitidas por el adaptador. El webhook no es alcanzable desde Internet en el
origen loopback actual. Con SMTP, la aceptación del servidor no prueba recepción.
[Verificación oficial de webhooks de Resend](https://resend.com/docs/webhooks/verify-webhooks-requests).

Antes de abrir el registro, verifica una cuenta de prueba autorizada: recibir el
correo, confirmar el enlace una vez, solicitar recuperación y comprobar que el
enlace vencido/reutilizado se rechaza. Consulta la entrega en Operación y correos.
No uses direcciones ajenas para las pruebas.

## Recorrido de aceptación de acceso social

| Caso | Resultado esperado |
| --- | --- |
| Registro con un correo nuevo verificado por el proveedor | Cuenta de candidato y pantalla de bienvenida; después completar perfil. |
| Volver con el mismo proveedor | Misma cuenta, sin duplicar perfil. |
| Correo ya registrado por otro método | Se solicita entrar por el método original y vincular desde Seguridad. No se fusionan cuentas. |
| Vincular desde Seguridad | Contraseña actual y MFA cuando esté activo; después autorización del proveedor. |
| Desvincular | Confirmación de acceso; conserva cuenta/perfil y revoca otras sesiones. |
| Cuenta social sin contraseña conocida | Establecer contraseña mediante Recuperar acceso antes de vincular/desvincular. |
| Cancelar consentimiento, vencer o usar otro navegador | No inicia sesión ni crea una vinculación. Permite reintentar. |
| Cuenta con MFA de TalentSync | Exige el segundo factor también al entrar con proveedor. |
| Registro empresarial | Conserva el flujo y permisos de empresa; los proveedores sociales son para candidatos. |

Las pruebas automatizadas verifican estos contratos con identidades sintéticas y
respuestas controladas. Los consentimientos reales siguen pendientes de comprobar
con cuentas autorizadas. La entrega de correo externo requiere todavía configurar
el remitente y el transporte correspondiente.
