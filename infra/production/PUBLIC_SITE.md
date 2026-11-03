# Sitio público y documentación para Google OAuth

La publicación informativa de TalentSync se compila por separado de la aplicación.
Incluye `/` y `/candidatos` para talento, `/empresas` para contratación,
funcionalidades de cada rol, `/privacidad` y `/terminos`. No muestra administración. No contiene
AuthProvider, cliente API, login, registro, credenciales ni bandeja de correo.
Mientras falta el servidor productivo, informa de que el acceso a cuentas está en
preparación. No utiliza la antigua API Azure como alternativa.

## Datos y compilación

Los datos de contacto autorizados para publicación se guardan en
`.local/public-legal.json` (ignorado por Git). Son datos públicos, no credenciales.
Campos: `NAME`, `EMAIL`, `CITY`, `COUNTRY`, `ADDRESS`, `PHONE`,
`EFFECTIVE_DATE` (AAAA-MM-DD). La dirección, el teléfono y el nombre se muestran
en la política. No introducir secretos en estos campos o en variables `VITE_*`.

Desde la raíz:

```powershell
./scripts/prepare-public-site.ps1
cd frontend
npx playwright test --config playwright.public.config.js
```

El script restaura el entorno del proceso después de compilar. La compilación de
publicación exige todos los campos. `-Draft` permite preparar un borrador que se
identifica como tal; nunca debe usarse como política definitiva. La salida es
`frontend/public-dist`, ignorada por Git. Se copian solo los recursos de marca y
se generan cabeceras CSP para el sitio informativo, sin permisos para la API Azure.
Además se genera HTML con el contenido completo de las cinco rutas, títulos,
metadescripciones, URL canónica, sitemap y robots. La documentación puede leerse
sin JavaScript. El módulo de renderizado temporal queda en
`frontend/.public-render`, ignorado por Git y fuera del directorio publicado.

La aplicación completa también tiene las rutas legales y enlaces en sus landings y
formularios de acceso. Su compilación debe recibir los mismos campos públicos.
`vite.config.js` admite las siete variables `VITE_LEGAL_*` o, en este equipo,
los siete campos autorizados de `.local/public-legal.json`; no incorpora integraciones
privadas ni el objeto completo de variables de entorno.
La publicación de una política no sustituye el consentimiento de registro ni
constituye una certificación de cumplimiento normativo.

## Cloudflare Pages

Proyecto existente: `talentsync-ai`. Antes de sustituir su despliegue, verificar el
estado anterior y conservar su identificador para una reversión desde Pages.
Subir únicamente `frontend/public-dist`. No subir `.local`, archivos `.env`,
fuentes, bases de datos o directorios del backend. Verificar HTTPS, recursos de
marca, rutas directas y cabeceras tras publicar.

El script anterior `deploy-cloudflare.ps1` corresponde a la aplicación con API
Azure; no sirve para esta publicación informativa.

Publicación comprobada el 27 de octubre de 2026:
- https://talentsync-ai.pages.dev
- https://talentsync-ai.pages.dev/candidatos
- https://talentsync-ai.pages.dev/empresas
- https://talentsync-ai.pages.dev/privacidad
- https://talentsync-ai.pages.dev/terminos

Las cinco rutas responden por HTTPS. Los enlaces y el dominio se guardaron en
Google Auth Platform del proyecto `talentsync-educacion`, junto con el contacto
`talentsyncadmin@gmail.com`. El 27 de octubre se verificó la propiedad en Search
Console mediante la etiqueta HTML de `frontend/index.html`, con la cuenta
propietaria del proyecto. No eliminar esa etiqueta en futuras publicaciones.
El consentimiento OAuth se cambió a **En producción**, con autorización del
responsable. Google todavía muestra pendientes las verificaciones de marca y
acceso a datos sensibles; no se ha presentado una solicitud de revisión completa.
El sitio verificado y el consentimiento publicado son estados distintos de la
aprobación de permisos por Google.
Se declararon los permisos realmente utilizados: `openid`, `userinfo.email`,
`userinfo.profile`, `calendar.events.owned` y `gmail.send`. Declararlos no concede
acceso a nuevas cuentas: cada conexión sigue requiriendo autorización del titular.

## Google

Inicio y política deben estar en el mismo dominio y ser accesibles sin cuenta.
Configurar solo URLs comprobadas en Branding y verificar propiedad del dominio
que Google solicite mediante Search Console. No dar por hecha la verificación
de `pages.dev`: comprobar el dominio privado registrable que acepte Google.

Publicar el consentimiento OAuth no equivale a tener la marca ni los permisos
verificados. Declarar todos los permisos realmente utilizados por acceso social,
Calendar y correo; atender los requisitos de verificación que muestre Google.
No eliminar clientes existentes ni ampliar permisos como atajo.

Después de salir del modo Prueba se renovó la autorización de correo, se verificó
la identidad del remitente y se comprobó una renovación de acceso sin enviar
mensajes. Google no devolvió una expiración de siete días para esta concesión.
Esto no garantiza duración ilimitada: una revocación o las políticas de Google
pueden invalidarla. Se conservaron respaldos privados de la configuración previa
y se reinició y comprobó el servidor de desarrollo con la nueva autorización.
No enviar más mensajes de prueba sin autorización.

Fuentes de requisitos:
- https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification
- https://developers.google.com/terms/api-services-user-data-policy
- https://cancilleria.gov.co/normograma/compilacion/docs/ley_1581_2012.htm
- https://sedeelectronica.sic.gov.co/politica-de-tratamiento-de-datos-personales

## Antes de habilitar cuentas públicamente

Falta verificar alojamiento del backend, mismo origen para sesiones/CSRF, callbacks
OAuth definitivos, contratos de
proveedores, conservación/rotación de copias y pruebas con datos productivos.
Neon y R2 preparados no equivalen a un servidor desplegado. No presentar la
publicación informativa como plataforma completa en producción.

## Aceptación legal de registro

Implementada para candidato, empresa, invitaciones y finalización del registro social.
Dos decisiones explícitas, comprobadas por el servidor y versionadas en
`backend/legal_documents/current.json`. Aplicar `alembic upgrade head` antes de
habilitar el frontend actualizado. La migración 0053 añade evidencia de autorización
sin atribuir aceptaciones a cuentas previas. La exportación de datos incluye esa evidencia.
Consultar `backend/legal_documents/README.md` para el cambio de versiones.

La imagen Docker de la aplicación copia el manifiesto compartido antes de compilar
React y exige los siete argumentos públicos `--build-arg VITE_LEGAL_<CAMPO>=...`.
El valor de cada argumento se toma del campo autorizado correspondiente de
`.local/public-legal.json` o de las variables públicas del entorno de construcción.
No pasar claves de OAuth, correo, base de datos o almacenamiento como argumentos
de compilación ni como variables `VITE_*`. Una imagen sin esos datos públicos
falla antes de compilar, para evitar abrir un registro enlazado a una política borrador.

## Estado pendiente de Google

El logotipo y las URLs públicas están guardados y el dominio está verificado.
La consola continúa sin ofrecer el botón de verificación de marca; en el centro de
verificación, «Preparar para la verificación» aparece deshabilitado. No se ha
sorteado ese control ni enviado una solicitud de revisión. Las capturas de estado
están en `.local/google-branding-logo-saved.png` y
`.local/google-verification-blocked.png`. El bloqueo de la consola y la ausencia
de backend público deben resolverse antes de abrir las cuentas.

Validación del cambio: 75 pruebas de autenticación y autorización legal, 73 de
migraciones, exportación y correo, 245 pruebas unitarias de frontend y recorridos
Playwright para registros, landings y documentos. Compilaciones completa y pública
correctas. La migración 0053 se aplicó a SQLite y Neon con respaldo previo y sin
modificar los registros existentes. Docker no está instalado en este equipo: se
validó el YAML de CI y el empaquetado de fuentes; la construcción de la imagen
queda para el trabajo `container` de CI. No se enviaron correos adicionales.
