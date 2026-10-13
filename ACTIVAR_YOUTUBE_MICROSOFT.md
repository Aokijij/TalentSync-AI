# Activar YouTube y Microsoft Learn en TalentSync local

Revisión: 13 de octubre de 2026. Los conectores están implementados. La activación real depende de tus credenciales y del acceso concedido por cada proveedor. No necesitas publicar TalentSync ni comprar un dominio para estas consultas desde el backend local.

## 1. YouTube

1. Entra en [Google Cloud Console](https://console.cloud.google.com/) con tu cuenta de Google.
2. Selecciona o crea un proyecto, por ejemplo `TalentSync Educación`.
3. Abre **APIs y servicios → Biblioteca**, busca **YouTube Data API v3** y pulsa **Habilitar**.
4. En **APIs y servicios → Credenciales → Crear credenciales**, elige **Clave de API**.
5. Edita la clave. En **Restricciones de API**, selecciona únicamente **YouTube Data API v3**. Nuestro conector consulta desde el servidor Python: una restricción de sitios web/referentes HTTP no corresponde a este flujo. Si dispones de una IP pública de salida fija, puedes restringir también por esa IP.
6. Guarda la clave únicamente en `.local/backend.env`, conservando los demás valores del archivo:

```dotenv
YOUTUBE_LEARNING_ENABLED=true
YOUTUBE_API_KEY=tu_clave_real
YOUTUBE_LEARNING_DAILY_REQUESTS=100
```

7. Reinicia el backend con los comandos del apartado 3.
8. Entra como administrador y abre **Catálogo educativo → Fuentes y conectores → YouTube**.
9. Pega el enlace de una lista pública que contenga vídeos. Consulta la vista previa, revisa la muestra y redacta la ficha editorial con utilidad, habilidades e idiomas reales. Incorpórala primero como borrador.
10. Vuelve a **Biblioteca**, filtra por **Sin publicar**, edita la ficha y publícala cuando esté revisada.

La lectura de listas públicas utiliza una clave de API; no requiere configurar un inicio de sesión OAuth de candidatos. Este conector no descarga vídeos ni busca masivamente. Cada vista previa realiza dos solicitudes. El límite local cuenta solicitudes por proceso y día UTC; no sustituye la cuota asignada al proyecto por Google. Consulta **APIs y servicios → YouTube Data API v3 → Cuotas** para ver tus límites reales.

Si recibes un rechazo, comprueba que la API está habilitada en el mismo proyecto de la clave, que sus restricciones permiten la API y que la cuota sigue disponible. Una lista privada o vacía no sirve para esta prueba.

Referencias: [Inicio de YouTube Data API](https://developers.google.com/youtube/v3/getting-started), [lectura de listas](https://developers.google.com/youtube/v3/docs/playlists/list), [restricciones de claves](https://docs.cloud.google.com/api-keys/docs/add-restrictions-api-keys).

## 2. Microsoft Learn con tu directorio Entra

Microsoft documenta una API autenticada con Entra y sin cargo por el uso de la API. El antiguo catálogo sin autenticación inició su retirada en junio de 2026. TalentSync usa la API nueva; no depende del endpoint antiguo.

1. Entra en el [centro de administración de Microsoft Entra](https://entra.microsoft.com/) y selecciona el directorio correcto.
2. Abre **Identidad → Aplicaciones → Registros de aplicaciones → Nuevo registro**. Según la versión del portal, puede aparecer directamente en **Entra ID → Registros de aplicaciones**.
3. Usa un nombre como `TalentSync Learn Local` y el tipo **Solo cuentas de este directorio organizativo**. Este conector usa la identidad de la aplicación, sin inicio de sesión de usuario; no necesita URI de redirección.
4. En **Información general**, copia el **Id. de aplicación (cliente)** y el **Id. de directorio (inquilino/tenant)**.
5. En **Certificados y secretos → Secretos de cliente → Nuevo secreto de cliente**, crea un secreto con vencimiento adecuado a tu revisión. Guarda su **Valor**, no el identificador del secreto. El portal solo muestra el valor al crearlo.
6. Configura únicamente el archivo privado `.local/backend.env`:

```dotenv
LEARN_ENABLED=true
LEARN_TENANT_ID=id_del_directorio
LEARN_CLIENT_ID=id_de_aplicacion
LEARN_CLIENT_SECRET=valor_del_secreto
```

7. Reinicia el backend y abre **Catálogo educativo → Fuentes y conectores → Microsoft Learn**.
8. Consulta **Módulos**, inicialmente sin filtro de producto. El backend obtiene un token con `https://learn.microsoft.com/.default` y consulta el catálogo en español cuando esté disponible.
9. Selecciona pocos recursos, impórtalos como borradores y revisa sus habilidades desde **Biblioteca → Sin publicar → Editar**. Después puedes consultar rutas o filtrar por `power-bi` o `azure`.

Tener Entra permite registrar la identidad; la consulta real confirma si Microsoft autoriza su acceso a Learn. El estado **Configurado** solo confirma la presencia de credenciales. Si aparece 401/403, comprueba el tenant, la vigencia y el valor del secreto, y el acceso de esa identidad a Learn Platform API según el proceso de incorporación de Microsoft. No añadas permisos de Microsoft Graph esperando que concedan acceso a Learn: son recursos distintos. No uses el permiso delegado `PublicContent.Read.All` como si fuese un permiso de aplicación; este conector no usa el flujo delegado.

La guía rápida oficial presenta un escenario con cuenta y suscripción Azure activa. Utiliza tu directorio existente; estos pasos no crean máquinas, almacenamiento ni despliegan TalentSync. La API entrega metadatos y enlaces, no el contenido completo ni la verificación automática de los certificados del candidato.

Referencias: [Disponibilidad y requisitos de Microsoft Learn Platform API](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-catalog), [autenticación y acceso de aplicación](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-get-started), [referencia de la API](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-catalog-endpoints-developer-reference), [guía rápida oficial](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-catalog-quickstart).

## 3. Reiniciar y comprobar

En la terminal que ejecuta el backend, pulsa Ctrl+C. Desde la raíz del proyecto, inicia:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py backend
```

Conserva el frontend abierto en [TalentSync local](http://127.0.0.1:5173) y recarga con Ctrl+F5. Cada conector muestra su configuración y permite una consulta manual para comprobar el acceso real. No hay claves en el frontend. No pegues secretos en el chat, capturas, archivos VITE_* ni Git.

Si deseas aplazar una integración, conserva sus credenciales en el archivo privado y cambia solo su bandera `*_ENABLED` a `false`; reinicia el backend. El catálogo ya incorporado permanece disponible.
