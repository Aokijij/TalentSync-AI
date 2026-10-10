# Primera etapa de integraciones

Implementación local del 10 de octubre de 2026. Sin crear cuentas externas,
aprovisionar recursos de Azure ni contratar planes. No se han enviado correos.

## GitHub: proyectos públicos

Habilitado en esta máquina mediante `GITHUB_PROJECT_ANALYSIS_ENABLED=true` en
`.local/backend.env`. Reiniciar el backend después de cambiar la configuración.

Recorrido del candidato: **Mi perfil → Evidencias de mi experiencia → Consultar
GitHub**. Introduce la URL raíz de un repositorio público y autoriza la consulta.
Revisa las tecnologías, describe tu aporte y confirma tu participación para
guardar la evidencia. Añadir tecnologías al perfil es una opción separada.

Se guarda la revisión exacta del repositorio y un resumen del análisis. La
presencia de archivos/dependencias no verifica autoría, ejecución ni dominio
profesional. No se clona ni ejecuta código, no se accede a repositorios privados
y no se utilizan los tokens del acceso social.

Límites: 2.000 entradas, 32 manifiestos de 256 KiB, respuesta de 1 MB,
presupuesto de 50 llamadas HTTP por hora y proceso, caché de 10 minutos con
hasta 32 proyectos. Estos límites son conservadores para un MVP con un solo
proceso; GitHub puede limitar antes por compartir IP con otras aplicaciones.
Las evidencias guardadas no se sincronizan automáticamente al cambiar el repo.

Los adaptadores existentes de acceso social Google/GitHub se conservan. Para
activarlos se necesita registrar una aplicación con el proveedor y configurar
su identificador/secreto; no hace falta migrar los usuarios ni la base de datos.
Con el origen local actual, los retornos son:

- `http://127.0.0.1:5173/api/v1/auth/social/github/callback`
- `http://127.0.0.1:5173/api/v1/auth/social/google/callback`

El frontend local reenvía `/api` al backend. Usar exactamente el mismo origen
en `PUBLIC_APP_URL` y en el proveedor. El acceso social necesita sesiones
habilitadas, como en el entorno aislado actual.

## Microsoft Learn: catálogo con revisión editorial

Ruta: **Administración → Catálogo educativo → Microsoft Learn**.
El conector permanece desactivado hasta disponer de una aplicación de Microsoft
Entra con acceso a Learn. La API vigente requiere autenticación; no utiliza el
antiguo catálogo anónimo.

En `.local/backend.env`, configurar en privado:

```dotenv
LEARN_ENABLED=true
LEARN_TENANT_ID=<UUID del directorio>
LEARN_CLIENT_ID=<UUID de la aplicación>
LEARN_CLIENT_SECRET=<secreto de la aplicación>
```

El secreto se queda en el servidor. No introducirlo en el chat ni en variables
`VITE_*`. El backend solicita un token con el ámbito
`https://learn.microsoft.com/.default` mediante credenciales de aplicación y lo
conserva temporalmente en memoria. No crea recursos de Azure.

1. Consultar módulos o rutas. El producto es opcional (`power-bi`, `azure`, etc.).
2. Seleccionar recursos de una página e importar como borradores.
3. Revisar cada borrador desde **Editar**: título, descripción, tiempo y, sobre
   todo, habilidades. Las etiquetas de producto son una sugerencia inicial.
4. Activar el recurso para que se ofrezca a candidatos.

La paginación se solicita manualmente; no se descarga el catálogo completo.
Las vistas previas caducan a los diez minutos y pertenecen al administrador que
las creó. Importar otra vez el mismo identificador conserva el recurso existente
y sus cambios editoriales. No hay sincronización automática ni eliminación
automática de recursos que el proveedor retire. Antes de publicarlos, revisar
también que sus condiciones siguen vigentes.

Se conservan proveedor, identificador, idioma, versión de API y fechas de origen
y consulta. No se importan alumnos ni resultados. Este catálogo no demuestra
que una persona completó la formación y no verifica certificados.

La conexión real queda pendiente de credenciales y comprobación con la cuenta
autorizada. Se probaron respuestas simuladas basadas en el contrato oficial.

## Resend: transporte de correo preparado

Implementado como alternativa a SMTP sobre la bandeja de salida existente:
reservas por trabajador, reintentos limitados, caducidad de enlaces y limpieza
del cuerpo después de enviar. Los errores no exponen la respuesta del proveedor
ni las credenciales. Cada mensaje utiliza una clave de idempotencia estable.

El usuario todavía no tiene dominio propio. Por ello no se activó Resend y
`scripts/local.py` fuerza **correo local**, sin usar claves externas heredadas.
No se envían los mensajes de las cuentas ficticias a Internet.

Para una activación futura fuera del lanzador aislado se necesitarán una cuenta
de Resend, dominio/remitente verificado y una prueba a un destinatario autorizado:

```dotenv
LOCAL_MAIL_ENABLED=false
SMTP_ENABLED=false
RESEND_ENABLED=true
RESEND_API_KEY=<clave privada>
RESEND_FROM=acceso@dominio-verificado.com
```

Solo puede activarse un transporte. La configuración no prueba entrega efectiva.
Resend aplica sus propias cuotas y condiciones; el conector no impone un límite
de gasto en la cuenta del proveedor. Mantener el plan gratuito y sus límites al
activarlo. La idempotencia del proveedor dura 24 horas; una recuperación manual
fuera de ese plazo requiere revisar el estado antes de reenviar.

## Validación y siguientes conexiones

Pruebas automáticas: permisos de rol, consentimiento, aislamiento de vistas
previas, selección de señales, deduplicación, conservación de ediciones,
límites de respuesta, redirecciones, errores sanitizados, configuración de
correo e idempotencia. Las pruebas aíslan credenciales y usan transportes
simulados; no envían correo ni dependen de los proveedores.

Resultado: 512 pruebas backend aprobadas y una omitida para PostgreSQL staging;
28 pruebas frontend aprobadas, lint Python/JavaScript y build de producción
correctos. La API local se comprobó con cuentas ficticias: vista previa real de
GitHub, Microsoft Learn pendiente de credenciales, correo exclusivamente local
y revisión sin segundo factor. Evidencia sin secretos en
`.local/verification/integrations-api.json`.

La revisión visual del navegador quedó pendiente porque su política de acceso
bloqueó la pestaña local; no se considera validada la apariencia interactiva.

Quedan para otras etapas: YouTube curado, oferta oficial SENA/Sapiencia,
Codewars opcional, registros empresariales autorizados, fuentes salariales
con cobertura comprobada, calendarios y validación de certificados por emisor.
No se debe inferir fraude por ausencia de logo o de un registro en una fuente
incompleta, ni acreditar competencias a partir de un contador de commits.

Referencias oficiales:

- [Autenticación y paginación de Learn](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-get-started)
- [Contrato del catálogo de Learn](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-catalog-endpoints-developer-reference)
- [Preguntas frecuentes y coste de Learn](https://learn.microsoft.com/en-us/training/support/integrations-learn-platform-api-faq)
- [Envío de correo con Resend](https://resend.com/docs/api-reference/emails/send-email)
- [Idempotencia de Resend](https://resend.com/docs/dashboard/emails/idempotency-keys)
- [Límites de GitHub REST](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
