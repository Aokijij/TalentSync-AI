# Staging: preparación de la infraestructura

Este bloque prepara **la base de infraestructura**, separado de producción, en
`rg-talentsync-staging`. No publica la aplicación ni envía correos. El lanzador
solo compila y calcula `what-if`; no contiene comandos de creación de recursos.

**Presupuesto actual: cero.** No activar esta infraestructura facturable.
La aplicación y las integraciones simuladas continúan ejecutándose localmente.
La plantilla queda guardada para una etapa futura con presupuesto autorizado.

```powershell
./scripts/staging-plan.ps1 -Mode Build
./scripts/staging-plan.ps1 -Mode Preview
```

Usa Azure CLI instalada o la copia portátil del proyecto y su directorio `.azure`.
Requiere Bicep instalado (`az bicep install`) y sesión Azure válida para Preview.
La contraseña del preview es ficticia; la plantilla declara ese parámetro seguro
y no devuelve secretos. Los informes y ARM compilado se guardan en `.local/staging`.
Los cambios previstos deben pertenecer exclusivamente al grupo de staging.

## Recursos propuestos y coste

| Recurso | Configuración inicial |
| --- | --- |
| PostgreSQL Flexible Server | 18, Standard_B1ms, 32 GiB con crecimiento automático, backups 7 días, sin HA |
| Red y DNS | VNet dedicada, subred para Container Apps y subred delegada para PostgreSQL; base sin acceso público |
| Container Apps | Entorno con perfil Consumption; todavía sin aplicación/revisiones |
| Registro de imágenes | ACR Basic, usuario administrador deshabilitado |
| Documentos | Blob Standard LRS, contenedor privado, HTTPS/TLS 1.2 mínimo, claves compartidas desactivadas, retención de borrado 7 días |
| Identidad | Identidad administrada con AcrPull en el registro y acceso de datos únicamente al contenedor cvs |
| Logs | Log Analytics, retención 30 días, límite de ingesta diario 1 GB |

La creación generará cargos, especialmente por PostgreSQL, registro y operación
del entorno/red, además de almacenamiento y logs según consumo. El límite de
ingesta no es un presupuesto total. Antes de crear, acordar presupuesto, región,
alertas y estimación vigente; el preview no cotiza ni garantiza capacidad/cuotas.
El crecimiento automático del almacenamiento también puede aumentar el coste.
No se configuró alta disponibilidad ni recuperación geográfica en este ensayo.

Las referencias empleadas son los esquemas oficiales de
[PostgreSQL Flexible Server](https://learn.microsoft.com/en-us/azure/templates/microsoft.dbforpostgresql/2024-08-01/flexibleservers),
[Container Apps](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2025-01-01/managedenvironments)
y [redes de Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/vnet-custom).
El acceso a ACR utiliza
[identidad administrada](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull).

## Aplicación: fase siguiente

La imagen sirve frontend y API desde una URL HTTPS única, con Vite `/api/v1`.
Separar `pages.dev` de `containerapps.io` rompe la sesión/CSRF actual. El ejemplo
`backend.env.example` usa `ENVIRONMENT=staging`: se rechazan sesiones inseguras,
host comodín, origen separado y PostgreSQL sin TLS; docs y buzón local quedan ocultos.

Antes de publicar falta completar y comprobar:

1. Activar y verificar el adaptador SMTP existente con un proveedor y dominio
   remitente autorizados. Outbox/reintentos se prueban con transporte simulado;
   todavía no se ha entregado correo real. El buzón local no envía correo.
2. Aprovisionamiento del rol PostgreSQL de aplicación sin privilegios de admin,
   desde un trabajo dentro de la red privada; almacenamiento/rotación de secretos.
   No abrir temporalmente la base a Internet ni pasar el administrador a FastAPI.
3. Imagen por commit, revisión de despliegue con probes y límites de escala,
   pruebas HTTPS/sesiones/CSRF, backups cloud y restauración. El Dockerfile actual
   lleva dependencias ligeras: no incluye los pesos neuronales de `.local`.
4. OAuth/SSO con callbacks reales y cuentas autorizadas; TURN y demás proveedores
   según se activen. Mantener desactivadas las integraciones sin credenciales.

Los scripts anteriores `deploy-azure.ps1` y `deploy-cloudflare.ps1` conservan
valores de producción y no son el lanzador de este nuevo entorno.

## Ensayo PostgreSQL local reproducible

```powershell
backend/.venv/Scripts/python.exe scripts/staging_postgres.py check
```

Requiere PostgreSQL 18 (ruta Windows predeterminada o `TALENTSYNC_PG_BIN`). Crea
su propio clúster en `.local/staging/pgdata`, puerto 55432, escucha IPv4 loopback,
autenticación SCRAM y rol de aplicación sin superusuario/creación de roles/bases.
Comprueba la propiedad mediante `SHOW data_directory` antes de administrar el
servidor. Nunca lee `backend/.env` ni utiliza la base/servicio PostgreSQL existente.
La conexión loopback del ensayo no usa TLS; la configuración externa sí lo exige.

Cada ejecución crea dos bases con nombres únicos, sintéticas: migraciones desde
cero, aceptación HTTP entre roles con sesiones/MFA, downgrade/upgrade de la última
revisión y backup/restore con comparación de todas las filas de todas las tablas.
La prueba lee únicamente sus correos sintéticos directamente del fixture: el
endpoint de buzón permanece cerrado sobre PostgreSQL. Los backups, datos y
credenciales quedan ignorados en `.local`; no elimina bases de ensayos anteriores.
Se detiene el servidor si lo arrancó esa ejecución. Un servidor ya activo y propio
se conserva; uno ajeno en ese puerto provoca rechazo.

El informe `verification.json` contiene etapas, versión, cabecera y huella de
código, sin contraseñas ni contenido de las filas. Una prueba deliberadamente
fallida no imprime errores SQL, que podrían incluir datos privados. Los checks
no equivalen a pruebas de carga o de recuperación del servicio Azure.

## Correo preparado sin contratar servicios

El bloque 27 añade SMTP STARTTLS o TLS implícito con validación de certificado,
outbox persistente, reintentos con espera creciente y máximo cinco intentos.
Las confirmaciones, recuperaciones e invitaciones usan esa cola solo si
`SMTP_ENABLED=true`. Configura `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`
(`starttls` o `ssl`), `SMTP_FROM` y, conjuntamente, usuario/contraseña si procede.
El worker solo arranca al activar SMTP; no existe modo de envío sin cifrado.
El lanzador local fuerza SMTP desactivado, aunque haya variables heredadas.

La migración 0036 conserva mensajes anteriores como `local`: activar SMTP en el
futuro no enviará el histórico. Cada envío reclama un lease de dos minutos antes
de contactar con el transporte; otro worker no puede finalizar un lease ajeno.
Se recuperan leases abandonados, no se envían enlaces vencidos y se vacía el cuerpo
al terminar, fallar definitivamente o caducar. Los errores almacenados son
categorías, sin texto del proveedor, tokens o credenciales; no se registran
excepciones SQL/SMTP completas. Los tests nunca se conectan a SMTP real.

La entrega es al menos una vez: si el proveedor acepta un mensaje y el proceso
falla antes de confirmar en la base, un reintento puede duplicarlo. Se conserva
un Message-ID estable para ese mensaje, sin garantizar deduplicación del proveedor.
Los leases coordinan workers; no existe una transacción distribuida con SMTP.
Downgradear 0036 elimina los metadatos de entrega; hacerlo solo con la cola
drenada, workers detenidos y backup, para no perder mensajes pendientes.

La implementación usa [smtplib](https://docs.python.org/3/library/smtplib.html)
y [ssl.create_default_context](https://docs.python.org/3/library/ssl.html#ssl.create_default_context)
de Python. No se instaló ni contrató un servidor SMTP. Se mantienen los correos
sintéticos en la bandeja de desarrollo para usar toda la aplicación local.
