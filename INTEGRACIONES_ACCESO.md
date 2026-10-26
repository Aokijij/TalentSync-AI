# Activar acceso social, Google Calendar y correo

## Revisión del acceso y las preferencias · 26 de octubre de 2026

- Google: la validación del ID token permite 30 segundos de desfase entre relojes.
  Se observó una diferencia de aproximadamente medio segundo con `time.google.com`;
  la tolerancia anterior era cero. Se siguen validando firma, emisor, audiencia,
  nonce, fechas y correo verificado. Referencia: [tolerancia de reloj en PyJWT](https://pyjwt.readthedocs.io/en/latest/usage.html).
- Las cuentas nuevas creadas mediante Google o GitHub deben confirmar su nombre
  profesional, profesión o cargo de interés y la correspondencia de estos datos
  en `/completar-cuenta`. El nombre admite caracteres internacionales y rechaza
  números y símbolos de alias. Esto recoge una declaración de identidad, no una
  verificación documental del nombre.
- La API bloquea el acceso al resto de funcionalidades mientras el registro esté
  pendiente y excluye esas cuentas de la búsqueda de candidatos. El estado persiste
  entre sesiones. La migración `0052_social_registration` deja todas las cuentas
  existentes como completadas; no obliga a repetir el registro al vincular un proveedor.
- Login y registro redirigen a las personas con sesión hacia su propio espacio.
  El formulario que está completando un acceso conserva su destino de bienvenida,
  invitación o segundo factor. La navegación final reemplaza la entrada del historial.
- «Ajustar mi búsqueda» abre `/preferencias`, con los mismos controles de modalidad,
  salario, sector y disponibilidad de Mi perfil. La bienvenida presenta un acceso
  breve a la guía. Al guardar se consulta el perfil más reciente y se modifican
  únicamente los campos editados.
- «Usar mi perfil» reconoce los títulos ocupacionales de ingeniería y tecnología
  además de los nombres de sus carreras. El editor de empresa ocupa el ancho
  disponible y conserva su adaptación a móvil.

Validación de esta revisión: pruebas aisladas del servidor y del navegador,
incluidos registro pendiente, CSRF/origen, retorno del proveedor, cuentas existentes,
navegación con Atrás, guardado tras errores y adaptación con texto al 200 %.
La migración se ensayó sobre registros sintéticos y se aplicó al entorno de trabajo
con copia previa y comprobación de conservación de registros. No se completó una
nueva autorización externa real durante esta revisión.

## Estado actual

El acceso de candidatos muestra Google y GitHub para registro, inicio de sesión y
vinculación. LinkedIn se retiró de estas pantallas y de las opciones públicas; los
enlaces profesionales de LinkedIn del perfil se conservan.

Se comprobó un inicio de sesión real con Google hasta abrir el panel del candidato.
La comprobación real de GitHub queda para el propietario, que prefirió probarla
posteriormente en su navegador. Sus flujos de vinculación y acceso tienen pruebas
automatizadas, y ahora muestran referencias de error específicas sin exponer datos
ni respuestas privadas del proveedor.

Google Calendar quedó conectado después de añadir la cuenta del propietario como
usuario de prueba en Google Auth Platform y completar el consentimiento autorizado.
Se verificaron la renovación del token y una respuesta 200 de Calendar API con una
consulta que no solicitó contenido de eventos. No se crearon eventos de prueba.

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

## LinkedIn: retirado del acceso

No aparece en registro, login, cuentas conectadas ni en las opciones públicas de
acceso. El adaptador previo permanece sin anunciar para una posible reactivación
futura; no se borran datos de proveedores ni enlaces profesionales de los perfiles.

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
respuestas controladas. Google y la conexión de Calendar también tienen comprobación
real; GitHub queda pendiente de la prueba del propietario. La entrega de correo
externo requiere todavía configurar el remitente y el transporte correspondiente.
