# Desarrollo local por bloques

Rama: `codex/desarrollo-funcionalidades-local`. Sin despliegues ni push.

## Arranque aislado

Desde la raíz, con Python disponible (o `backend/.venv/Scripts/python.exe`):

```powershell
backend/.venv/Scripts/python.exe scripts/local.py setup
backend/.venv/Scripts/python.exe scripts/local.py seed
backend/.venv/Scripts/python.exe scripts/local.py accounts
backend/.venv/Scripts/python.exe scripts/local.py backend
```

En otra terminal, desde `frontend/`:

```powershell
$env:VITE_API_URL='/api/v1'
npm run dev -- --host 127.0.0.1
```

Abre http://127.0.0.1:5173. Vite reenvía `/api` al backend local en 8000.
Los archivos `.env` existentes no se modifican. La base, archivos y credenciales
ficticias se guardan en `.local/` (excluido de Git). La semilla es idempotente y
rechaza cualquier base distinta de la SQLite aislada. Azure y sincronizaciones
externas permanecen desactivados, incluso si existen variables heredadas.

## Versionamiento

Cada bloque se confirma después de sus pruebas y revisión del diff. Las migraciones
son aditivas y se comprueba generación SQL de PostgreSQL además de SQLite.
Las integraciones sin credenciales deben mostrarse como no configuradas; no se
simulan accesos sociales, certificados, probabilidades o llamadas externas.

## Bloques y alcance

| Bloque | Alcance | Estado |
| --- | --- | --- |
| 1 | Entorno aislado, semilla ficticia e historial de eventos | Completado: 71 pruebas backend, 20 frontend, lint y build |
| 2 | Correo local, recuperación, verificación, sesiones, MFA y privacidad | Implementado y probado; adaptadores sociales y SSO en bloques posteriores |
| 3 | Verificación empresarial, equipos y permisos | Implementado: revisión manual local, borradores, invitaciones y permisos en API |
| 4 | Requisitos, evidencias, preferencias y matching avanzado | Implementado; modelo neuronal local activado y verificado en bloque 20 |
| 5 | Historial de etapas, plazos, avisos y feedback | Implementado: plazos, worker local, cierre idempotente e historial |
| 6 | Brechas, recursos, planes, evaluaciones, pasaporte y portafolio | Implementado con catálogo de proyectos y evaluaciones locales de fundamentos |
| 7 | Selección ciega, calidad de vacantes y contratación por potencial | Implementado: identidad protegida, reglas locales y escenarios laborales |
| 8 | Reputación, incidencias, auditoría y tendencias | Implementado y probado con métricas internas y revisión de incidencias |
| 9 | Entrevistas y colaboración | Implementado: editor, pizarra, versiones y señalización WebRTC local |
| 10 | Personalización, evaluación de modelos e integraciones | Implementado localmente; estado y dependencias externas documentados |
| 11 | Acceso social de candidatos | Google y GitHub implementados con proveedores simulados en pruebas; requieren credenciales para uso real |
| 12 | Vinculación de cuentas sociales existentes | Implementado con reautenticación, MFA y control de sesión; sin conexión externa real |
| 13 | Análisis estático de proyectos | Implementado por ZIP local, vista previa y evidencia no verificada con incorporación opcional al perfil |
| 14 | Catálogo educativo y transparencia comercial | Administración, importación JSON, brechas y planes integrados; sin compras ni certificados automáticos |
| 15 | Acceso y vinculación LinkedIn | Adaptador OIDC implementado y probado en memoria; desactivado sin credenciales y HTTPS |
| 16 | Lectura de repositorios públicos GitHub | Adaptador con consentimiento, revisión fija y límites; desactivado localmente por defecto |
| 17 | SSO administrativo de Google Workspace | Aprovisionamiento local, validación de dominio y sujeto, MFA y política obligatoria opcional |
| 18 | Retos SQL con consultas reales | Dos retos, vista previa, ejecución restringida en memoria y pasaporte integrado |
| 19 | Conectividad STUN/TURN de entrevistas | Configuración validada, credenciales temporales y autorización por sala; servidor externo no configurado |
| 20 | Modelo semántico multilingüe en CPU | Pesos fijados y verificados, inferencia offline activa y caché acotada |
| 21 | Cierre de revisión e inventario | 249 pruebas backend, 20 frontend, lint completo, build y recorrido SQL en navegador |
| 22 | SSO administrativo de Microsoft Entra ID | Tenant fijo, identidad aprovisionada, MFA y sesiones vinculadas a la aplicación; 290 pruebas backend y 20 frontend |
| 23 | Aceptación completa entre roles y aprendizaje | Flujo integrado con sesiones, MFA, verificación, selección ciega, práctica SQL, entrevista, plazos, privacidad y auditoría |
| 24 | Diagnóstico, verificación repetible y entrega local | Comandos doctor/verify, informe sin secretos, comprobación de pesos configurados y documento de transición |

## Comprobaciones

```powershell
backend/.venv/Scripts/python.exe scripts/local.py test
backend/.venv/Scripts/python.exe scripts/local.py doctor
backend/.venv/Scripts/python.exe scripts/local.py verify
# Desde frontend/: npm test; npm run lint; npm run build
```

El flujo de eventos acepta únicamente metadatos escalares permitidos. No contiene
contraseñas, tokens, CV completos ni respuestas privadas de entrevistas. Cada evento
se guarda en la misma transacción de la operación que describe.

`scripts/local.py test` fuerza una base en memoria y desactiva pesos neuronales,
OAuth, lectores externos, STUN/TURN y tareas de mantenimiento, aunque estén activos
en el entorno de demostración. Las pruebas configuran sus propias dependencias y
bases temporales. No modifica `.local/backend.env`. La inferencia real se comprueba
por separado con `model-check` y mediante el servidor local. Las advertencias de
SQLAlchemy se tratan como errores; las advertencias de deprecación existentes no
se expanden en el resumen de ejecución.

## Bloque 2: acceso local

El lanzador aislado activa sesiones opacas revocables mediante cookie HttpOnly,
CSRF por sesión y cookies sin `Secure` exclusivamente en desarrollo HTTP local.
Producción siempre fuerza `Secure`. El modo JWT anterior permanece disponible
por defecto para compatibilidad, pero está desactivado en el entorno aislado.
Empresas y administradores deben configurar TOTP antes de operar. El secreto se
cifra en reposo; los códigos de recuperación se guardan como hashes y son de un
solo uso. La recuperación de contraseña conserva MFA y revoca las sesiones.

La bandeja `/desarrollo/correos` solo funciona con la opción local activada,
SQLite y acceso de loopback. Contiene enlaces temporales sensibles de prueba;
no es un servicio de correo ni debe exponerse a redes externas.

Los botones sociales permanecen desactivados sin credenciales. Los adaptadores y
la vinculación se incorporaron posteriormente en los bloques 11, 12, 15 y 17.

Validación del bloque: 77 pruebas backend en conjunto; 11 pruebas de seguridad,
arquitectura y migración repetidas tras endurecer el consumo de códigos MFA;
lint y build frontend. Se comprobó en navegador el login del candidato,
persistencia al navegar y pantalla de seguridad. La semilla utiliza direcciones
ficticias bajo el dominio reservado example.com.

## Bloque 3: organizaciones

`/empresa/equipo` reúne verificación, invitaciones de tres días y asignaciones.
`/admin/verificaciones` permite aprobar, pedir información, rechazar o suspender
con un motivo. Las nuevas empresas locales requieren correo confirmado y revisión
manual antes de publicar o consultar talento. Suspender pausa sus vacantes activas.
Las empresas anteriores conservan su acceso para una migración gradual.

Cada cuenta empresarial pertenece a una organización en esta versión. El propietario
gestiona la identidad y el equipo; el reclutador gestiona selección; el entrevistador
solo consulta las vacantes asignadas con alias de candidatos. Cambiar permisos revoca
las sesiones anteriores. Los borradores solo son visibles a la empresa y al admin.
Las invitaciones están ligadas al correo, almacenadas como hash y se consumen una vez.
La revisión local no consulta registros oficiales ni equivale a una verificación legal.

## Bloque 4: compatibilidad explicable

`/compatibilidad` permite al candidato comparar requisitos ponderados (esenciales
y deseables), preferencias imprescindibles y evidencias de portafolio. La empresa
edita allí los requisitos. Las bases relacionadas del grafo se muestran separadas:
Java no acredita Spring Boot y Spring Boot no acredita microservicios.
Los enlaces aportados son declaraciones; no se descargan ni se verifican solos.

Cada recomendación conserva versión del algoritmo, huella de sus entradas,
contribuciones al resultado y brechas. El caché detecta cambios del candidato y de
la vacante. La interfaz usa los pesos del servidor, incluidos idiomas y formación.
El porcentaje es un índice de afinidad; las preferencias se comparan aparte para
no alterar el mérito técnico. El componente textual actual usa HashingVectorizer
local de respaldo se identifica como lexical-hashing-v1. El bloque 20 activa un modelo neuronal; no se presenta como un modelo
neuronal ni una probabilidad de éxito. El procesamiento de CV existente se conserva.
Validación acumulada: 81 pruebas backend; lint y build frontend aprobados.

## Bloque 5: seguimiento y plazos

`/procesos/:id` presenta el historial real de cambios, feedback público y plazo
de respuesta. Las notas internas no se exponen. Nuevas postulaciones reciben
un plazo de siete días naturales por avance, configurable en la API entre 1 y 30.
Los procesos anteriores conservan su estado sin imponerles plazos retroactivos.
El candidato puede retirarse conservando el historial.

El lanzador local activa una revisión cada minuto, independiente de sincronizaciones
externas. Emite un recordatorio el día anterior y cierra una sola vez al vencer.
El aviso distingue falta de respuesta de una evaluación del candidato. Las
actualizaciones del proceso usan control de versión para evitar sobrescrituras.
La revisión se ejecuta al volver a encender el backend; no funciona con el equipo
apagado. También puede ejecutarse con POST /api/v1/admin/workflow/run.
Las métricas de estos vencimientos alimentarán reputación en el bloque 8.
Las empresas no pueden eliminar postulaciones ni vacantes con procesos para borrar
el historial. La acción anterior de eliminar pasa a finalizar y notificar, conservando
los registros. Se mantiene el borrado administrativo y el endpoint anterior del
candidato; su interfaz normal usa la retirada con conservación del historial.

## Bloque 6: aprendizaje dirigido

`/aprendizaje` contiene brechas por oferta, proyectos locales, planes persistentes,
escenarios de mejora del índice y pasaporte de fundamentos. La estimación examina
hasta 200 vacantes activas y usa el mismo motor de compatibilidad; no promete
contrataciones. Marcar un proyecto terminado no acredita conocimientos.

Hay micropruebas originales de Python, SQL y microservicios (cinco preguntas, diez
minutos, umbral del 80%, repetición tras 24 horas). El servidor controla el tiempo,
oculta las respuestas y consume una sola vez cada intento. La aprobación añade la
habilidad al perfil y conserva el alcance "fundamentos", la versión y vigencia de
180 días. No equivale a una certificación profesional ni prueba código arbitrario.
La finalización de recursos externos, títulos y compras no se simulan. Catálogos
educativos y afiliación siguen desactivados hasta disponer de integraciones reales.
Validación acumulada: 85 pruebas backend; lint y build frontend aprobados.

## Bloque 7: selección y calidad

Las nuevas vacantes activan selección ciega por defecto. Antes de la entrevista
se muestran alias por vacante, habilidades y resultados compartidos. La API
oculta nombres, perfiles completos, fotos y respuestas libres, incluidos avisos
de nuevas postulaciones. Avanzar a entrevista o selección registra la apertura
de identidad. Vacantes anteriores conservan su comportamiento para migración gradual.

`/empresa/calidad` revisa requisitos contradictorios, información salarial y
restricciones personales mediante reglas explícitas. Las referencias salariales
requieren cinco ofertas comparables de esta misma base y se etiquetan como locales.
No representan el mercado en tiempo real. Permite añadir escenarios de decisiones
del trabajo al flujo de postulación existente, conservando su categoría. No hay
diagnóstico de personalidad ni puntuación psicológica.

El buscador de talento distingue bases relacionadas de habilidades acreditadas
y muestra evaluaciones de fundamentos solo si el candidato comparte evidencias.
Validación acumulada: 87 pruebas backend; lint y build frontend aprobados.

## Bloque 8: confianza y salud del ecosistema

`/confianza` permite reportar incidencias sobre procesos propios. El relato original
solo lo ven su autor y administración; la empresa recibe un resumen revisado y puede
apelar. Las denuncias pendientes no penalizan. El índice considera respuestas y
vencimientos observados durante 90 días, suaviza muestras pequeñas y reduce la
visibilidad con cinco observaciones y puntuación menor de 60, o dos incidencias
confirmadas. Apelar conserva la incidencia hasta resolverla. No certifica empresas.

`/admin/ecosistema` compara oferta de habilidades y perfiles de esta base, registra
auditorías por versión, comprueba invariancia ante metadatos de identidad y compara
distribuciones con PSI cuando hay al menos veinte pares. Estas pruebas no demuestran
ausencia de sesgos; los grupos demográficos no se evalúan sin datos consentidos.
El cálculo textual utiliza evidencia profesional y elimina identificadores conocidos;
los textos libres pueden conservar información personal no identificada. No usa el
embedding antiguo del CV completo para calcular afinidad. Los datos ficticios locales
no se presentan como estadísticas del mercado ni capacidad predictiva validada.

## Bloque 9: entrevistas colaborativas locales

`/entrevistas` permite al equipo preparar una sala por proceso en entrevista técnica.
El candidato recibe un aviso y ambos acceden al editor de texto y pizarra. Publicar
comparte una versión; cada tres segundos se consultan cambios. Si existen cambios
locales, una nueva versión no los sobrescribe. Se puede descargar el código antes
de reemplazar el borrador. La empresa puede cerrar la sala y conservar lo publicado.
Los entrevistadores requieren una asignación vigente; cada petición valida acceso.

La videollamada usa WebRTC directo con señalización autenticada por HTTP cada 1,5
segundos, dos pestañas, presencia de 90 segundos y señales que caducan a los 60.
La cámara y el micrófono solo se solicitan al pulsar el botón. No se graban medios.
Funciona en localhost con navegadores compatibles; sin STUN/TURN no garantiza
conectividad entre redes distintas. Las señales pueden incluir datos de red y se
eliminan al cerrar la sala o en la siguiente limpieza de conexiones. Una base apagada
puede conservar señales caducadas hasta esa limpieza; nunca se entregan caducadas.

El editor no ejecuta código en el host. Un ejecutor arbitrario necesita contenedores
aislados, límites y un adaptador específico. Los documentos persisten localmente;
no hay edición carácter a carácter ni resolución automática de conflictos (CRDT).
Las pruebas verifican permisos, versiones, cierre, tamaño de mensajes, caducidad,
privacidad de señales y retirada de asignaciones. La verificación audiovisual real
requiere dos navegadores y permisos de cámara/micrófono del usuario.

## Bloque 10: personalización y evaluación de modelos

`/mis-intereses` guarda una decisión por candidato y vacante, solo con consentimiento.
Permite ocultar ofertas, deshacer decisiones y retirar todas las interacciones al
desactivar la personalización en Seguridad. No registra navegación. La señal
colaborativa usa similitud de habilidades declaradas y exige tres candidatos
consentidos distintos por oferta. No entrega identidades de vecinos. Ordena dentro
de bandas de diez puntos de afinidad, conservando el índice técnico y el nivel de
reputación. El historial permite recuperar ofertas ocultas. Se procesan como máximo
las 5.000 decisiones más recientes por consulta.

`/admin/modelos` muestra método activo, datos disponibles y experimentos persistentes.
La regresión logística aprende interés declarado con seis características numéricas;
no aprende ni ofrece probabilidades de contratación. Se requieren cien decisiones,
veinte candidatos, diez vacantes y veinte casos de cada respuesta. Se excluyen cuentas
de dominios de ejemplo o `.test`. La evaluación separa usuarios con semilla fija 42
y compara AUC/Brier con una referencia constante. Los coeficientes y parámetros se
guardan como JSON, fuera del ranking. Un resultado favorable en una partición pequeña
no demuestra capacidad de generalización ni ausencia de sesgos.

El lanzador activa una revisión horaria: solo entrena con datos suficientes, como
máximo una vez al día y si cambiaron los datos. No inventa muestras. Eliminar señales
o retirar consentimiento elimina los artefactos aprendidos que pudieran incluirlas;
se conservan métricas históricas agregadas. El control de sesgos demográficos y una
eventual promoción de modelos al ranking necesitan validaciones adicionales.

### Embeddings neuronales opcionales

Este bloque añadió el adaptador opcional. El bloque 20 instaló sus dependencias,
descargó una revisión fijada y comprobó inferencia real en CPU. El entorno aislado
actual usa el modelo multilingüe local; sin MATCH_MODEL_PATH usa lexical-hashing-v1.
Las pruebas comprueban que no admite nombres remotos ni formatos ejecutables.

Para activarlo posteriormente: instalar `backend/requirements-model-local.txt`,
proporcionar un modelo compatible en una carpeta absoluta y añadir
`MATCH_MODEL_PATH=C:/ruta/al/modelo` a `.local/backend.env`. Debe contener
`modules.json`, módulos estándar Transformer/Pooling/Dense/Normalize y pesos
safetensors, sin archivos Python, pickle o binarios PyTorch. Un error de configuración
impide el arranque; no hay sustitución silenciosa. La huella de archivos identifica
el método y cambia las versiones de caché, feedback y auditorías. El parser de CV y
sus vectores antiguos se conservan; la comparación neuronal calcula ambos textos
con el mismo modelo.

La carga usa `local_files_only=True`, `trust_remote_code=False` y modo offline según
la [documentación oficial de Sentence Transformers](https://sbert.net/docs/package_reference/sentence_transformer/model.html).
La dependencia opcional está fijada a [6.1.0 en PyPI](https://pypi.org/project/sentence-transformers/6.1.0/).

### Alcance que sigue pendiente

Los bloques 14 a 20 incorporan catálogo administrable, LinkedIn, lectura pública
de GitHub, SSO Workspace, retos SQL, configuración STUN/TURN y modelo neuronal.
Quedan fuera del uso local las compras/acuerdos educativos, registros oficiales,
servidor TURN operativo y ejecución arbitraria de código. Los proveedores de
identidad requieren credenciales; no se conectaron cuentas externas reales.
VPN, dominios separados y restricciones de red corresponden a infraestructura futura.
No se crean microservicios para esta versión: se extienden los módulos y puertos del
FastAPI/React existente para preservar compatibilidad. No hay despliegue ni push.

Validación acumulada tras el bloque 11: 128 pruebas backend y 20 frontend; lint y build aprobados.
Las pruebas de migraciones cubren una base SQLite nueva, actualización desde una
versión anterior y generación SQL PostgreSQL sin conexión. Esto no sustituye probar
las migraciones contra un servidor PostgreSQL real antes de un despliegue futuro.

## Bloque 11: acceso social de candidatos

Se implementaron adaptadores OAuth de GitHub y Google sobre las sesiones revocables
existentes. Solo crean cuentas de candidato. Las empresas conservan su registro,
verificación y MFA; el acceso administrativo permanece independiente. Los proveedores
se desactivan por defecto y los botones muestran su disponibilidad real.

Para habilitar uno, registra una aplicación en ese proveedor y configura únicamente
sus variables en `.local/backend.env`, que está excluido de Git:

```dotenv
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
```

Reinicia el backend después de cambiar configuración. El lanzador no hereda claves
OAuth del sistema: solo acepta las de este archivo aislado. Registra exactamente
estas URL de retorno; navega desde `127.0.0.1:5173`, sin alternar con `localhost`:

- GitHub: `http://127.0.0.1:5173/api/v1/auth/social/github/callback`
- Google: `http://127.0.0.1:5173/api/v1/auth/social/google/callback`

El retorno pasa por el proxy de Vite para conservar el origen de las cookies. En
otra instalación, `PUBLIC_APP_URL` debe ser el origen público de la aplicación,
con proxy para `/api`; se exige HTTPS excepto en loopback de desarrollo. No hay
redirecciones configurables por el visitante. Activar el proveedor permite al
candidato autorizar explícitamente el acceso en su página externa.

Cada autorización utiliza PKCE S256 y estado aleatorio ligado a una cookie HttpOnly
de ese navegador. El estado vence en diez minutos, se consume atómicamente antes
del intercambio y el verificador cifrado se borra al consumirlo. Los intentos
vencidos se limpian al iniciar el siguiente acceso. Google valida firma RS256,
emisor, audiencia, caducidad, nonce y correo verificado. GitHub exige el correo
principal verificado y consulta la identidad en cada acceso. Solo solicita perfil
y correo; no obtiene repositorios. Los tokens del proveedor no se guardan en la
base ni se entregan al frontend. El callback vuelve a rutas fijas y usa no-store
y no-referrer. Los registros HTTP del servidor/proxy deben excluir parámetros del
callback antes de una futura exposición pública, pues contienen códigos temporales.

La identidad estable del proveedor permite volver a entrar sin sobrescribir el
correo o nombre local. Si ese correo ya pertenece a otra cuenta, el acceso se
detiene y solicita el método original: no vincula cuentas automáticamente. El bloque
12 permite añadir proveedores desde Seguridad con reautenticación explícita.
Las cuentas nuevas reciben una contraseña aleatoria no entregada; pueden definir
una mediante Recuperar acceso y la bandeja local si necesitan funciones que exigen
confirmación con contraseña, como activar MFA o cambiar el correo.

El primer acceso termina en Bienvenida. Si el usuario ya activó MFA en TalentSync,
se exige el código o recuperación en `/acceso-social`, mediante un desafío HttpOnly
de cinco minutos y un uso, antes de emitir la nueva sesión de ocho horas. El acceso
social no activa por defecto una sesión persistente de treinta días.

Las pruebas usan proveedores simulados y transporte HTTP en memoria: cubren creación,
retorno, cookies y CSRF, rechazo de correo existente, identidad estable, MFA, borrado
en cascada, estados vencidos o repetidos, cancelación, fallos externos y validación
criptográfica de Google. No se registraron aplicaciones externas ni se probaron
cuentas reales: ambas integraciones permanecen desactivadas localmente.

Referencias del flujo: [GitHub OAuth](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
y [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect).

### Revisión de compatibilidad de los bloques anteriores

La regresión completa cubre acceso y sesiones, permisos y verificación empresarial,
compatibilidad explicada y preferencias, plazos y cierre de procesos, aprendizaje y
micropruebas, selección ciega, reputación y auditorías, salas y señalización, y
personalización consentida. Se ejecutó con los avisos de SQLAlchemy sobre relaciones
tratados como errores. Las migraciones verifican instalación nueva, actualización
y generación SQL PostgreSQL. También pasaron las pruebas frontend, ESLint y build.

Se corrigió un fallo transversal: ahora `flush`, al igual que `commit`, revierte
conflictos de unicidad o edición concurrente y devuelve 409, en vez de dejar la
sesión inutilizable o devolver 500. Dos pruebas comprueban que se puede continuar
usando la sesión tras el conflicto. Se versionó esta corrección por separado.

Quedan las comprobaciones externas y manuales ya indicadas: videollamada real entre
dos navegadores, inferencia con pesos neuronales reales, proveedores OAuth reales y
migraciones en PostgreSQL. Las pruebas locales no acreditan precisión predictiva,
ausencia de sesgos demográficos ni validación oficial de empresas o cursos.

## Bloque 12: vincular proveedores a cuentas existentes

Seguridad incluye Cuentas conectadas para candidatos en modo sesión. El usuario
confirma su contraseña actual y, si está activado, un código MFA o de recuperación
nuevo. Después autoriza Google o GitHub. Se conserva el perfil, correo y nombre de
TalentSync aunque el correo social sea diferente. La API solo muestra proveedor y
fecha de conexión; no entrega identificadores externos ni credenciales.

El intento conserva propósito, candidato y sesión inicial, además del estado,
cookie de navegador y PKCE del bloque 11. Se comprueba la vigencia de esa misma
sesión antes y después del intercambio externo. Cerrar sesión, cambiar de cuenta,
abrir otra sesión o revocar la original impide terminar. El callback no emite una
nueva sesión al vincular. Las cuentas sociales ya usadas por otra cuenta no se
transfieren; tampoco se reemplaza silenciosamente el proveedor existente.

Desvincular vuelve a exigir contraseña y MFA si corresponde. Mantiene la sesión
actual y el acceso por contraseña, cierra las demás sesiones y cancela vínculos y
desafíos MFA sociales pendientes. Funciona incluso si se desconfigura el proveedor.
No revoca autorizaciones en la página externa: estas se administran en Google o
GitHub. Si la cuenta se creó mediante acceso social, antes debe definir contraseña
con Recuperar acceso y el correo local. Las contraseñas no se guardan en el frontend
ni en eventos; los campos de confirmación se vacían al enviar.

La migración 0032 conserva los intentos anteriores como accesos de tipo `login`.
Se probaron actualización, reversión y nueva actualización sobre SQLite con estados
pendientes, y generación SQL PostgreSQL. Las pruebas cubren contraseña, MFA, CSRF,
roles, propietario, intentos de unir cuentas, revocación durante el intercambio,
desvinculación, cascadas y conservación del acceso por correo. No se conectaron
cuentas externas reales; siguen siendo necesarias las credenciales del bloque 11.

## Bloque 13: evidencias técnicas desde proyectos locales

Compatibilidad incluye Analizar un proyecto local. Permite cargar un ZIP propio o
descargado manualmente de GitHub, revisar las tecnologías detectadas, seleccionar
las que se quieren declarar y describir la contribución antes de guardar. La
semilla crea `.local/demo-project.zip` con un ejemplo ficticio de Python y
TypeScript; no sobrescribe un archivo existente. Puede usarse para probar la
pantalla con la cuenta candidata local.

El analizador `local-project-inspector-v1` cuenta extensiones de archivos y examina
dependencias conocidas en `package.json`, `requirements*.txt`, `pyproject.toml` y
`pom.xml`, además de la presencia de Dockerfile. No ejecuta código, instala
dependencias, extrae archivos al disco ni descarga enlaces. No lee el contenido de
los archivos fuente. Omite carpetas de dependencias, compilaciones y archivos
ocultos. Los manifiestos deben estar en UTF-8; los no interpretables producen un
aviso sin descartar las señales válidas del resto del proyecto.

Cada carga admite hasta 8 MiB comprimidos, 2.000 entradas y 32 MiB descomprimidos
declarados, con relación de compresión máxima 200:1 por entrada. Solo se aceptan
ZIP sin compresión o DEFLATE. Se leen como máximo 32 manifiestos de 256 KiB cada
uno. Se rechazan rutas absolutas, recorridos `..`, nombres ambiguos, enlaces,
cifrado y archivos corruptos. La profundidad máxima de rutas es veinte y cada
nombre completo tiene hasta trescientos caracteres. No se interpretan DTD ni
entidades externas XML. Una estructura JSON excesivamente anidada se trata como
manifiesto no interpretable.

`POST /api/v1/matching/projects/preview` recibe multipart `file` y devuelve hasta
veinte tecnologías, sus señales de origen, avisos y estadísticas. La vista previa
no modifica la base. Su token cifrado y autenticado se liga al candidato y vence
en diez minutos. `POST /api/v1/matching/projects/evidence` exige ese token,
selección de tecnologías detectadas y confirmación de participación. Ambos
endpoints requieren rol candidato; las sesiones de navegador exigen CSRF y
tienen un límite de veinte peticiones por hora y endpoint.

Al guardar se conserva el resumen técnico y la huella SHA-256 del ZIP, junto con
la descripción aportada por el candidato; no se conserva el ZIP, su contenido ni
sus rutas internas. La huella impide duplicados idénticos dentro del portafolio
actual. Se mantiene el límite de cincuenta evidencias. El resumen se puede abrir
en la evidencia guardada y eliminar usando el flujo existente. Los eventos solo
registran origen y versión del analizador.

Todas estas evidencias tienen `verified=false`: declarar una dependencia no
demuestra autoría ni competencia. Por defecto se conservan las habilidades del
perfil. Solo marcar Añadir las tecnologías seleccionadas incorpora esas
declaraciones y puede cambiar la afinidad. Guardar o eliminar evidencia invalida
la versión del matching. No se infiere que Spring Boot demuestre microservicios,
ni se presenta el resultado como probabilidad de contratación o certificación.
Las micropruebas del bloque 6 siguen siendo un mecanismo separado de evaluación.

La detección utiliza formatos documentados en
[npm](https://docs.npmjs.com/cli/configuring-npm/package-json/),
[PyPA](https://packaging.python.org/en/latest/specifications/pyproject-toml/) y
la biblioteca [zipfile de Python](https://docs.python.org/3.13/library/zipfile.html).
La consulta automática de repositorios GitHub sigue pendiente y no está autorizada
por conectar una cuenta social; el acceso del bloque 11 solo solicita perfil y
correo. También siguen pendientes las integraciones externas indicadas en los
bloques anteriores, sus credenciales y sus comprobaciones reales.

## Revisión acumulada de los bloques 12 y 13

Pasaron 164 pruebas backend, incluyendo migraciones y regresión de los bloques
anteriores, con avisos de relaciones SQLAlchemy tratados como errores. Pasaron las
20 pruebas frontend, Ruff, ESLint y la compilación de producción. El análisis de
proyectos tiene cobertura de límites, entradas inseguras, manifiestos corruptos,
privacidad del resumen, roles, CSRF, token alterado, caducado o de otro candidato,
incorporación opcional de habilidades, duplicados y portafolio lleno.

Se comprobó además por HTTP contra el servidor local el acceso con cuenta ficticia,
análisis del ZIP de ejemplo, guardado como evidencia no verificada, eliminación de
esa evidencia temporal y cierre de la sesión de prueba. Se corrigió el arranque
local para excluir pruebas, utilidades, migraciones y entorno virtual de la
recarga automática mediante rutas absolutas; el filtro se comprobó en Windows.
No se hicieron push, despliegues ni conexiones a cuentas externas.

## Bloque 14: catálogo educativo administrable

`/admin/aprendizaje` permite crear, editar, archivar e importar cursos, talleres y
documentación. Cada recurso incluye proveedor, enlace HTTPS, habilidades, duración
estimada, coste declarado y explicación de patrocinio o afiliación cuando aplica.
La API rechaza enlaces con credenciales, IP, HTTP o dominios locales. No consulta
esas URL ni compra cursos. Administración debe revisar disponibilidad, permisos de
uso y condiciones antes de publicarlos; el formulario no confirma acuerdos reales.

`GET/POST /api/v1/admin/learning/resources`, `PUT .../{id}` y `POST .../import`
requieren rol administrador y los controles de sesión/MFA/CSRF existentes. La
importación acepta una lista `resources` de hasta cincuenta objetos y se valida
antes de guardar; el catálogo admite hasta doscientos recursos administrables.
La edición envía `version` y rechaza cambios concurrentes con 409. Los ejercicios
originales permanecen disponibles y no se editan desde esta pantalla.

Aprendizaje muestra el catálogo, enlaces externos, declaraciones comerciales y
micropruebas de fundamentos disponibles para las habilidades de cada recurso.
Recomienda únicamente recursos que cubren una brecha. Examina hasta diez recursos,
preseleccionados por cobertura, horas e identificador, y doscientas vacantes; ordena
por mejora hipotética de afinidad por hora. El patrocinio o afiliación no participa
en ninguno de esos cálculos. Las horas y costes no se consultan en tiempo real.

Los planes se conservan al archivar recursos, pero no admiten incorporaciones
nuevas de esos recursos. Marcar un curso terminado no añade habilidades, aprueba
evaluaciones ni confirma certificados. Los enlaces no añaden identificadores de
candidato ni seguimiento de compras. La migración 0033 crea `learning_resources`.
Las pruebas cubren brechas, planes históricos, ausencia de acreditación automática,
edición concurrente, importaciones atómicas, publicidad y validación de enlaces.
La importación JSON permite trabajar localmente sin APIs de terceros; adaptadores
contractuales de proveedores y liquidación de comisiones requieren integración real.

## Bloque 15: LinkedIn para candidatos

El proveedor LinkedIn utiliza los mismos estados de un uso, cookie de navegador,
vinculación con reautenticación y sesiones del bloque 11/12. Valida JWT RS256 contra
las claves del endpoint fijo de LinkedIn, emisor, audiencia, caducidad, nonce y parte
autorizada; consulta userinfo con un token transitorio y exige que `sub` coincida
con el token firmado. Si falta correo verificado o nonce, rechaza el acceso. No
interpreta el acceso social como verificación legal ni importa el CV de LinkedIn.

Para configurarlo se necesitan `OAUTH_LINKEDIN_CLIENT_ID` y
`OAUTH_LINKEDIN_CLIENT_SECRET` en `.local/backend.env`, el producto Sign In with
LinkedIn using OpenID Connect autorizado por el proveedor y un `PUBLIC_APP_URL`
HTTPS con callback exacto `/api/v1/auth/social/linkedin/callback`. El lanzador local
mantiene su origen HTTP habitual, por lo que este proveedor sigue desactivado en
esa configuración. No se creó un túnel público ni se expuso la máquina. Una futura
configuración HTTPS debe conservar el proxy y origen de las cookies.

El adaptador envía PKCE S256 y exige un nonce de la transacción; la compatibilidad
real de esa aplicación debe comprobarse antes de habilitarla. No reduce estas
comprobaciones si un proveedor no entrega los datos necesarios. Doce pruebas
cubren autorización, tokens alterados, emisor, audiencia, nonce, caducidad, correo,
userinfo de otro sujeto y el flujo de candidato con estado consumido. También
pasaron las pruebas anteriores de Google, GitHub y vinculación. No se conectó
ninguna cuenta real. Referencias: [LinkedIn OIDC](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2)
y [flujo OAuth](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow).

## Bloque 16: analizar repositorios públicos de GitHub

Compatibilidad muestra una opción adicional cuando se configura
`GITHUB_PROJECT_ANALYSIS_ENABLED=true` explícitamente en `.local/backend.env` y se
reinicia el servidor. Por defecto es `false`, incluso si existe una variable
heredada. Cada consulta exige marcar autorización de acceso público; no se consulta
GitHub al cargar la página, conectar una cuenta social o navegar por el catálogo.
No se habilitó esta conexión ni se consultaron proyectos reales durante el desarrollo.

`POST /api/v1/matching/projects/github/preview` requiere candidato, CSRF de sesión,
`url` raíz del repositorio y `confirm_public_access=true`, con cinco consultas por
hora. Solo acepta `https://github.com/propietario/repositorio`, sin credenciales,
puerto, fragmento, subrutas ni parámetros. Construye solicitudes únicamente hacia
`https://api.github.com`; no sigue redirecciones, usa proxies heredados ni envía
tokens. Los repositorios privados no son accesibles mediante este adaptador.

Consulta el commit HEAD, fija su árbol por SHA y lee únicamente blobs de manifiestos
reconocidos por el bloque 13. Los nombres de otros archivos sirven para contar
extensiones; sus contenidos no se descargan. Omite enlaces, submódulos, dependencias
y archivos ocultos. Rechaza árboles truncados o de más de dos mil entradas,
manifiestos mayores de 256 KiB y más de treinta y dos manifiestos. Cada respuesta
se limita a un MiB, o cuatrocientos mil bytes para blobs. Hay timeout de ocho
segundos por operación y no se empiezan nuevas operaciones tras treinta segundos.
Un fallo no genera evidencia parcial ni descarga alternativas.

La vista previa y el guardado conservan el contrato cifrado de diez minutos del
bloque 13. Se añade la URL pública y revisión analizada al resumen; al guardar se
fija ese enlace para no atribuir el informe a otro repositorio. La huella de
repositorio y revisión detecta duplicados. Sigue siendo evidencia no verificada y
requiere confirmar participación. No ejecuta, clona ni guarda código fuente.
Diecinueve pruebas con transporte HTTP en memoria cubren límites, redirecciones,
URLs inseguras, cuota, repositorio privado, consentimiento, CSRF y guardado. No
demuestran autoría ni sustituyen la comprobación con una conexión real habilitada.
Referencia: [GitHub REST, árboles y blobs](https://docs.github.com/en/rest/git/trees)
y [commits](https://docs.github.com/en/rest/commits/commits).

## Bloque 17: acceso corporativo administrativo

El portal administrativo incluye Google Workspace cuando se configuran
`OAUTH_WORKSPACE_CLIENT_ID`, `OAUTH_WORKSPACE_CLIENT_SECRET` y `WORKSPACE_DOMAIN`
en `.local/backend.env`. Es una aplicación OAuth independiente del acceso Google
de candidatos. El dominio debe estar en minúsculas y ser exacto. Se valida la
afirmación firmada `hd`, además de firma, emisor, audiencia, nonce, caducidad y
correo verificado. No basta con que el correo termine en el dominio esperado.
Callback exacto: `http://127.0.0.1:5173/api/v1/auth/admin-sso/callback` para el
entorno local; una instalación externa debe usar HTTPS. No se configuraron claves
ni conectaron cuentas reales.

El sujeto estable de Google debe vincularse previamente a un administrador ya
existente. No existe registro público, aprovisionamiento por correo coincidente
ni elevación de roles. Desde la raíz, el operador local puede usar:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py admin-sso bind --email admin@empresa.com --subject SUJETO_ESTABLE_DE_GOOGLE
backend/.venv/Scripts/python.exe scripts/local.py admin-sso revoke --email admin@empresa.com
```

Estas acciones revocan las sesiones anteriores y registran eventos sin correo ni
sujeto. No reemplazan vínculos existentes silenciosamente. El operador debe obtener
el sujeto mediante una fuente autorizada del proveedor. No se ejecutaron estos
comandos contra las cuentas del usuario durante el desarrollo.

El flujo corporativo usa estados y cookies propios de diez minutos, PKCE y consumo
atómico antes del intercambio. Su segundo factor tiene un token independiente de
cinco minutos y un uso; vuelve a comprobar rol, sujeto aprovisionado y dominio
configurado. No admite el desafío del acceso social de candidatos. Si el administrador
aún no tiene MFA de TalentSync, solo puede entrar a Seguridad para configurarlo.
Las operaciones administrativas siguen bloqueadas hasta completar esa configuración.

`ADMIN_SSO_REQUIRED=true` activa la política obligatoria: rechaza nuevos accesos
administrativos por contraseña, JWT anteriores y sesiones de contraseña ya abiertas.
Las sesiones corporativas se identifican en servidor, sin depender del frontend.
La opción queda en `false` localmente para conservar el acceso existente mientras
no hay un proveedor configurado. La migración 0034 conserva sesiones anteriores
como `password` y añade contexto a los desafíos de autenticación.

Las pruebas cubren aprovisionamiento, ausencia de creación/elevación automática,
aislamiento de flujos, vínculo al navegador, CSRF/origen, MFA, caducidad, revocación,
cambio de dominio/rol y aplicación de la política a sesiones y JWT anteriores.
Este bloque incorporó Google Workspace; el bloque 22 añade Microsoft Entra ID.
VPN y restricciones de infraestructura no se han creado. Referencia:
[validación del dominio Google Workspace](https://developers.google.com/identity/openid-connect/openid-connect).

## Bloque 18: retos prácticos SQL

Aprendizaje incluye dos ejercicios originales: sumar pedidos pagados por cliente
y contar pedidos pagados conservando clientes sin coincidencias. El candidato
escribe una consulta SQLite, puede probarla con los datos visibles y entregar una
vez para evaluarla contra tres conjuntos ficticios, incluidos casos límite. Los
otros conjuntos y respuestas esperadas no se entregan al cliente. Las pruebas
rechazan una respuesta escrita de forma fija que solo satisface la muestra.

Cada reto tiene quince minutos, un intento nuevo por veinticuatro horas y exige
superar todas las comprobaciones. Se incorpora al pasaporte existente con alcance
de fundamentos SQL y vigencia de 180 días; no acredita experiencia profesional.
Una aprobación actualiza habilidades y caché, y respeta el consentimiento existente
para avisar a empresas. Completar cursos o pulsar Probar no concede acreditación.

El ejecutor crea una SQLite `:memory:` nueva por consulta, con tablas y datos propios.
No usa la conexión, archivos ni credenciales de TalentSync. Solo autoriza SELECT,
lectura de las tablas indicadas y una lista limitada de funciones. Deniega escritura,
ATTACH, PRAGMA, extensiones, lectura de archivos y consultas al esquema interno.
Aplica límites de cuatro mil caracteres, treinta y dos columnas, profundidad de
expresiones treinta, diez SELECT compuestos, diez mil instrucciones al compilar,
cien mil pasos de ejecución y doscientos milisegundos por consulta. Los resultados
tienen hasta cien filas y dieciséis KiB; no admite binarios ni números no finitos.
Cada conexión se cierra explícitamente. No es un ejecutor de Python, Java o shell.

La API `/api/v1/learning/practical` lista los retos; `/{challenge_id}/start` crea o
recupera el intento. `/attempts/{id}/preview` solo ejecuta la muestra, y
`/attempts/{id}/submit` consume el intento atómicamente antes de evaluar. Requiere
candidato, CSRF en sesiones y límites de peticiones. Los endpoints de preguntas
y de consultas no aceptan intentos del otro tipo. No se guarda el SQL enviado en
la base ni en eventos; el borrador solo vive en la página abierta.

Dieciséis pruebas nuevas cubren restricciones, límites, consultas reales,
respuestas fijas, aislamiento de candidatos, caducidad, CSRF, entrega repetida y
pasaporte. Pasaron también las pruebas de aprendizaje, catálogo y arquitectura.
Se reforzó la fábrica temporal de la suite para que retirar una dependencia
sobrescrita no permita recurrir a la base anterior. Referencia:
[autorización y límites de SQLite en Python](https://docs.python.org/3/library/sqlite3.html).


## Bloque 19: conectividad STUN/TURN

El navegador solicita `/api/v1/interviews/rooms/{id}/ice` antes de activar cámara
y micrófono. La API comprueba pertenencia actual a la sala y proceso abierto,
limita las peticiones y devuelve `Cache-Control: no-store`. El frontend entrega
esa configuración a RTCPeerConnection. No se solicitan permisos multimedia al
cargar la página.

La configuración explícita en `.local/backend.env` usa listas JSON, por ejemplo:
`WEBRTC_STUN_URLS=["stun:localhost:3478"]` y
`WEBRTC_TURN_URLS=["turn:localhost:3478?transport=udp"]`.
TURN exige `WEBRTC_TURN_SECRET` de al menos 32 caracteres, compartido con un servidor
compatible con TURN REST, como coturn. Nunca se incluye ese secreto en la respuesta.
Las credenciales se calculan con HMAC-SHA1, caducan en una hora y usan identificadores
aleatorios opacos. Una nueva activación obtiene credenciales nuevas. Una reconexión
posterior al vencimiento puede requerir desconectar y activar de nuevo.
`WEBRTC_RELAY_ONLY=true` obliga a retransmitir y requiere TURN configurado.

No se heredan estas opciones del entorno exterior al lanzador. Por defecto no
hay servidores STUN/TURN ni solicitudes a terceros. No se instaló un servidor de
retransmisión, no se probó conectividad entre redes externas y no se activaron
cámaras ni micrófonos durante la validación. La conexión directa sigue dependiendo
de la red; una instalación accesible por Internet requiere HTTPS y comprobar el
servidor elegido. Diez pruebas nuevas verifican configuración, HMAC, caducidad,
opacidad, pertenencia y cierre; pasaron también las de entrevistas y arquitectura.
Referencia: [coturn TURN REST](https://github.com/coturn/coturn/wiki/turnserver).


## Bloque 20: inferencia semántica multilingüe local

El entorno aislado tiene activo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`,
revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, con licencia Apache-2.0
según la ficha del editor. Los pesos y tokenizadores viven únicamente en
`.local/models/`, excluidos de Git. Se conservaron la ficha y procedencia local.
La huella calculada identifica el método como
`local-sentence-transformer:97473d94587537f6`.

Para reproducir, instalar las dependencias sin cambiar las versiones base:

```powershell
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-lite.txt -r backend/requirements-model-local-lock.txt
backend/.venv/Scripts/python.exe scripts/local.py model-prepare
backend/.venv/Scripts/python.exe scripts/local.py model-check
```

`model-prepare` es una descarga explícita de archivos públicos de esa revisión;
no envía perfiles, claves ni tokens de cuenta. Verifica tamaño y huella SHA-256
para archivos LFS, o la huella Git para archivos normales, antes de reemplazar
el destino. Solo descarga los doce archivos enumerados, sin Python ni pickle.
Es idempotente y no activa el modelo automáticamente. La procedencia se guarda
fuera de la carpeta del modelo para que no cambie su huella de inferencia.

Después de comprobarlo, añadir la ruta absoluta a `MATCH_MODEL_PATH` en
`.local/backend.env` y reiniciar. Esto ya se realizó en esta máquina. No se cambió
`backend/.env`. La carga durante el arranque usa solo archivos locales,
safetensors, módulos estándar y `trust_remote_code=False`; no descarga archivos.
Un fallo impide arrancar. Sin ruta configurada sigue disponible el método lexical.

La inferencia CPU usa dos hilos por defecto, ajustables entre uno y ocho mediante
`MATCH_MODEL_CPU_THREADS`. Una caché por proceso conserva hasta 512 pares de
huellas/vectores inmutables, sin texto original ni persistencia. Serializa la
inferencia para evitar saturación por peticiones simultáneas. La huella del modelo
participa en la versión de matching, caché de recomendaciones y señales de interés.
No cambia el parser ni interpreta relación semántica como habilidad acreditada.

La comprobación real offline obtuvo 100 para textos iguales, 95,53 para
"Desarrollo de aplicaciones web" / "Web application development" y 16,42 contra
una frase de jardinería. La primera carga y tres comparaciones tomaron 20,32 s,
incluida importación de librerías. Son ejemplos sintéticos de funcionamiento,
no una evaluación de precisión en contratación. El modelo preentrenado complementa
los requisitos explícitos, preferencias y explicaciones; el índice no es una
probabilidad de éxito ni garantiza equidad. Tres pruebas nuevas cubren integridad
de descarga, caché acotada, versiones y rechazo de módulos no admitidos.
Referencia: [ficha original del modelo](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).


## Bloque 21: revisión y cierre local

Se corrigió el selector del encoder para que la caché siga la ruta configurada,
sin conservar un resultado anterior cuando cambia la configuración de una prueba.
El comando `test` aísla también modelo, integraciones y mantenimiento. Dos pruebas
nuevas comprueban esos casos sin descargar ni cargar pesos. La suite final pasó
249 pruebas en 95,76 s, con avisos de deprecación existentes. Las siete pruebas
focalizadas de modelo, lanzador y arquitectura pasaron con SAWarning como error.

Se ordenaron imports existentes para dejar limpio el lint completo de backend,
scripts y tests. En Aprendizaje se retiraron identificadores internos de las
micropruebas y se permitió elegir otra evaluación cuando vence el intento actual.
Lint JavaScript y compilación Vite pasaron después de estos ajustes; las veinte
pruebas frontend también pasaron. `pip check` no detectó dependencias incompatibles.

Se comprobó por HTTP local el método neuronal, aprendizaje, pasaporte, entrevistas,
identidades vinculadas, denegación del panel administrativo a candidatos y logout.
En navegador una cuenta ficticia independiente resolvió el reto SQL, probó la
muestra, entregó y recibió la acreditación tras las tres comprobaciones. La captura
queda en `.local/verification/retos-sql.jpg`. No se cambiaron credenciales del usuario
ni se activaron permisos de cámara o micrófono. La migración de este bloque era 0034.
El inventario actual y sus dependencias externas están en [FEATURES_LOCAL.md](FEATURES_LOCAL.md).

## Bloque 22: SSO administrativo de Microsoft Entra ID

El mismo portal permite seleccionar Google Workspace o Microsoft Entra ID como
proveedor corporativo. El botón muestra el proveedor configurado; el acceso social
de candidatos sigue separado. Entra está desactivado en esta entrega porque no se
han configurado credenciales ni conectado cuentas reales. El acceso local por
contraseña conserva la política opcional anterior.

Para una organización con una aplicación confidencial **Web** registrada, estas
variables se pueden configurar explícitamente en `.local/backend.env`:

```dotenv
ADMIN_SSO_PROVIDER=entra
ENTRA_TENANT_ID=UUID_CANONICO_DEL_TENANT
OAUTH_ENTRA_CLIENT_ID=UUID_CANONICO_DE_LA_APLICACION
OAUTH_ENTRA_CLIENT_SECRET=SECRETO_DE_LA_APLICACION
```

Tenant y aplicación deben ser UUID en minúsculas, sin llaves. No se admiten
`common`, `organizations`, `consumers` ni URLs proporcionadas como tenant. Los
endpoints de autorización, token y claves se construyen exclusivamente bajo
`login.microsoftonline.com` para ese tenant. El intercambio de código ocurre en
FastAPI; no se debe registrar como aplicación SPA ni exponer el secreto en React.
Los ámbitos solicitados son `openid profile`, sin Graph ni renovación persistente.

Callback local exacto:
`http://127.0.0.1:5173/api/v1/auth/admin-sso/callback`.
Microsoft indica que las direcciones HTTP con `127.0.0.1` se registran mediante
`replyUrlsWithType` en el manifiesto de la aplicación, ya que el cuadro de texto
del portal las rechaza. No se admite loopback IPv6. Fuera de desarrollo se exige
HTTPS. El lanzador mantiene la URL local y no modifica aplicaciones de Azure.
Referencia: [URI de redirección de Microsoft](https://learn.microsoft.com/en-us/entra/identity-platform/reply-url).

Una cuenta administradora existente debe vincularse a la identidad estable
`tenant UUID:object UUID`, obtenida de una fuente autorizada del directorio:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py admin-sso bind --provider entra --email admin@empresa.com --subject TENANT_UUID:OBJECT_UUID
backend/.venv/Scripts/python.exe scripts/local.py admin-sso revoke --provider entra --email admin@empresa.com
```

No se crean usuarios, promueven roles ni vinculan por coincidencia de correo/UPN.
Los vínculos Entra y Workspace tienen espacios independientes; cambiar o retirar
un vínculo revoca las sesiones de esa cuenta. Estos comandos no se ejecutaron
contra cuentas del usuario durante el desarrollo.

Se validan firma RS256, clave de firma, emisor exacto, audiencia única, nonce,
vigencia, versión 2.0, tenant y objeto firmados. Los correos mutables no autorizan
el acceso. Se conservan PKCE, estado ligado al navegador, consumo único y MFA de
TalentSync. Si aún no hay MFA, la sesión solo permite configurar Seguridad.
Referencia: [afirmaciones del ID token de Microsoft](https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference).

La migración 0035 añade una huella del proveedor, tenant/dominio y aplicación a
las sesiones corporativas. El callback y el segundo factor rechazan cambios de
configuración durante el flujo. Una sesión corporativa presentada con otra
configuración se revoca y no revive al restaurar la anterior. Las sesiones
corporativas antiguas deben volver a autenticarse; las de contraseña se conservan.
No se guardan tokens de Microsoft ni sus secretos en eventos.

El lanzador ignora configuración corporativa heredada salvo valores explícitos
del archivo local; las pruebas fuerzan nuevamente proveedores desactivados.
Pasaron 290 pruebas backend, incluidas 39 de Entra, y 20 frontend; también lint
Python/JavaScript, build Vite, migraciones de subida/bajada y SQL PostgreSQL offline.
Se comprobó por HTTP local salud, opciones de SSO desactivadas, login de candidato,
perfil, catálogo y logout. La migración local aplicada es 0035. Las pruebas usan
firmas RSA y transporte en memoria; el login contra una organización real requiere
registrar y configurar su aplicación y aún no se ha verificado externamente.

## Bloque 23: aceptación local entre roles

La prueba `tests/test_local_acceptance.py` recorre el proceso con tres navegadores
HTTP independientes y una base temporal: registro, correo local, sesiones opacas,
CSRF y MFA real, revisión empresarial, publicación y reclutamiento ciego. Después
comprueba aprendizaje y una consulta SQL contra los tres conjuntos sintéticos,
pasaporte y aviso consentido a la empresa; continúa con revelación controlada,
feedback, editor/pizarra compartidos y conflicto de versión. Finalmente verifica
cierre por plazo, reputación, privacidad de incidencias, revisión administrativa,
auditoría, retirada de personalización, logout y recuperación MFA de un uso.

Las cuentas, documentos y procesos son ficticios. Solo el fixture de esa base
aprovisiona al administrador; el registro público sigue sin permitir ese rol.
La prueba no utiliza cuentas de `.local`, tokens JWT anteriores ni proveedores
externos. Comprueba que consultas SQL, código, claves y detalles privados no
aparezcan en metadatos de eventos.

Se corrigió la proyección de aprendizaje para excluir la vacante seleccionada
del número de **otras vacantes** examinadas y beneficiadas. La interfaz aclara
ese alcance; las ofertas pausadas no se cuentan. Cuatro pruebas focalizadas
de aprendizaje y aceptación pasaron después del cambio.

## Bloque 24: comprobación y transición de la versión local

`doctor` comprueba la instalación, entorno aislado, integridad y cabecera de la
SQLite local sin escribir filas. Descubre revisiones Alembic normales y anotadas;
la ausencia de servidores en ejecución se informa como aviso. No lee `backend/.env`
ni muestra credenciales. `verify` ejecuta pip check, Ruff, pytest aislado, pruebas
Node, ESLint y Vite, y comprueba inferencia real si hay pesos configurados. El
comando del modelo ahora usa `MATCH_MODEL_PATH`, evitando validar otra carpeta.

La verificación falla ante errores y cambios de código durante su ejecución.
Guarda resultado, duración de etapas y huella de archivos en
`.local/verification/validation.json`; doctor escribe `doctor.json`. Ninguno
contiene credenciales o perfiles. Las pruebas de estas herramientas usan carpetas
y bases temporales, simulan los procesos de verificación y comprueban migración
atrasada, base corrupta, configuración externa, pesos ausentes y parada ante fallos.

El alcance terminado, comandos y dependencias para pasar a integración están en
[LOCAL_HANDOFF.md](LOCAL_HANDOFF.md). El entorno local conserva las cuentas, la
base aislada y la migración 0035. No se activaron proveedores, infraestructura,
correo real, cámara o micrófono ni se ejecutó código arbitrario en el host.

## Bloque 25: ensayo PostgreSQL y configuración segura de staging

`scripts/staging_postgres.py check` usa PostgreSQL 18 en un clúster propio,
loopback puerto 55432, SCRAM y rol de aplicación sin privilegios administrativos.
No conecta al servicio PostgreSQL anterior ni lee su configuración. Cada ensayo
usa bases sintéticas nuevas; aplica todas las migraciones, recorre la aceptación
entre roles con sesiones/MFA, baja/sube la última revisión y restaura un backup.
Compara todas las filas de las 27 tablas, incluidas sesiones y eventos. Los datos
y credenciales quedan en `.local/staging`, fuera de Git y del contexto Docker.
Se evita capturar `pg_ctl` con pipes en Windows porque el daemon hereda esos
handles y la lectura puede quedar esperando EOF. Se detiene solo el clúster
propio si lo arrancó esa ejecución; los ensayos previos se conservan.

`ENVIRONMENT=staging` exige HTTPS de mismo origen, sesiones seguras, host explícito,
buzón local desactivado y PostgreSQL con TLS. Oculta documentación y añade HSTS.
Docker excluye `.local`, que podía entrar en el contexto remoto de construcción,
y desactiva logs de acceso para evitar registrar códigos de callbacks OAuth.
El runner local y los valores de producción existentes se conservan.

Pasaron 319 pruebas backend y siete adicionales de protección del lanzador; la aceptación PostgreSQL pasa por separado
y se omite en el runner SQLite habitual. El ensayo PostgreSQL 18.4 pasó con
subida/bajada y restauración exacta de las 27 tablas. Todavía no se ha construido
ni ejecutado la imagen Docker en este equipo; no hay Docker/Podman disponible.

## Bloque 26: plantilla y vista previa de infraestructura

`infra/staging` contiene Bicep separado de producción para PostgreSQL 18 privado,
VNet/DNS, entorno Container Apps Consumption, ACR Basic sin usuario administrador,
Blob privado con identidad administrada y Log Analytics. El rol de datos se
limita al contenedor de documentos; la contraseña PostgreSQL es parámetro seguro
y no aparece en outputs. `scripts/staging-plan.ps1` compila o ejecuta `what-if`
con parámetro ficticio; no contiene despliegue, publicación o creación de recursos.

Bicep 0.48.1 compiló la plantilla. La vista previa Azure en eastus2 devolvió
Succeeded, 15 creaciones y ningún cambio fuera de `rg-talentsync-staging`.
El catálogo de capacidades de la región incluye PostgreSQL 18. Estos resultados
no garantizan capacidad, cuota o coste de despliegue. No se creó el grupo ni se
publicó la aplicación. Los informes quedan en `.local/staging`.

El README de staging describe los recursos facturables y la siguiente fase:
correo externo con reintentos, rol PostgreSQL de aplicación y secretos, imagen y
revisión HTTPS, pruebas reales de proveedores y restauración Azure. El buzón
local no entrega correo; la plantilla de infraestructura no es un despliegue
completo de la aplicación y no reutiliza los scripts antiguos de producción.

## Bloque 27: correo SMTP y continuación con presupuesto cero

El usuario indicó presupuesto cero. No se activan recursos facturables ni se
publica la aplicación; la plantilla del bloque 26 se conserva para el futuro.
Las siguientes comprobaciones usan los runtimes y PostgreSQL ya instalados.

Se añadió un puerto de entrega de correo y adaptador SMTP con STARTTLS/TLS
implícito, certificado/hostname verificados antes de autenticar y sin logs de
contenido. Configuración incompleta, modo sin cifrar y mezcla SMTP/buzón local
se rechazan. Los errores de Settings ocultan valores de entrada. El lanzador
local fuerza SMTP desactivado y elimina credenciales SMTP heredadas.

La migración 0036 amplía `mail_messages` con estado, intentos, lease, plazos y
categoría de fallo. Conserva el histórico como local. Los flujos de confirmación,
recuperación/cambio de correo e invitación encolan para el transporte elegido.
El worker SMTP, desactivado por defecto, reclama con UPDATE condicional y confirma
la transacción antes de la red; recupera leases abandonados y reintenta errores
temporales con espera creciente, hasta cinco intentos. Descarta enlaces vencidos
y elimina cuerpos al finalizar. No guarda texto privado de errores del proveedor.

Las pruebas cubren TLS antes de AUTH, certificados, errores 4xx/5xx, recuperación
tras caída, espera/reintentos agotados, leases y rechazo de un worker antiguo,
expiración y registro sin envío síncrono. La aceptación PostgreSQL añade dos
conexiones concurrentes que compiten por un mensaje y verifica recuperación del
lease. Se prueban migraciones con correos existentes, subida/bajada y restauración.
El envío externo permanece sin verificar: no se conectó ningún SMTP real ni se
envió correo a personas. La entrega permite duplicados si el proceso cae después
de la aceptación SMTP; Message-ID estable no garantiza entrega exactamente una vez.

## Bloque 28: ampliación de práctica local y validación de respuestas

Se incorporaron micropruebas originales de APIs REST, Git y seguridad de
aplicaciones, con cinco preguntas cada una y sus proyectos de práctica. El
catálogo ofrece seis evaluaciones de fundamentos y seis proyectos locales.
Se añadieron dos retos SQL, informe de totales/promedios y último pedido por
cliente, para un total de cuatro. Todos conservan tres conjuntos sintéticos,
ejecución de solo lectura, plazos, entrega única y alcance de fundamentos.

Las respuestas de micropruebas ahora exigen enteros estrictos y una opción dentro
del rango de cada pregunta. Una entrada inválida no consume el intento. La
caducidad usa el mismo límite inclusivo que el resto de los retos. Pasaron 43
pruebas focalizadas de aprendizaje, catálogo y consultas SQL, incluidos entrega,
pasaporte, privacidad, controles de acceso y rechazo de respuestas inválidas.
# Bloque 29 — ensayo local completo sin presupuesto

`scripts/local.py rehearse` reúne `verify`, PostgreSQL real aislado y `doctor`.
Comprueba que los informes correspondan a la misma huella de código y escribe
`.local/verification/rehearsal.json`, sin secretos. PostgreSQL requiere la
instalación local ya detectada; no usa la base original ni crea recursos externos.

Se añaden conexiones SMTP SSL/STARTTLS reales contra un sumidero exclusivo en
127.0.0.1: certificado confiable de prueba, rechazo de CA desconocida y rechazo de
hostname incorrecto antes de enviar credenciales. No se desactiva la validación TLS
ni se entrega correo fuera del equipo.

La prueba de capacidad usa ocho candidatos simultáneos, 50 ofertas sintéticas,
sesiones independientes, CSRF y escrituras aisladas en una SQLite temporal con
WAL. Guarda latencias y estados HTTP en `capacity.json`; mide ASGI dentro del
proceso, matching léxico y limitador desactivado, sin representar una capacidad
de producción. La matriz `matching-regressions.json` comprueba orden por cobertura,
invariancia ante identificadores, alias, duplicados, componentes y confianza de
ofertas externas. No estima éxito de contratación ni equidad demográfica.
# Bloque 30 — cierre y verificación visual

Inventario actualizado a seis micropruebas y cuatro retos SQL. Documentación del
ensayo unificado, límites de capacidad y dependencias externas que siguen
desactivadas con presupuesto cero. Las pruebas del runner comprueban que se
detenga ante un fallo y rechace informes correspondientes a otro código.

Revisión de navegador con cuentas QA locales ficticias independientes: candidato,
entrega del reto de totales/promedios y pasaporte, acceso empresarial y
administrativo con MFA, paneles y catálogo educativo. Sin cambiar las cuentas
de demostración previas ni activar permisos audiovisuales. Los informes actuales
y su huella están en `.local/verification/` y `.local/staging/verification.json`;
el inventario por rol está en `FEATURES_LOCAL.md`.
# Bloque 31 — dependencias de construcción sin avisos conocidos

La auditoría adicional detectó avisos de denegación de servicio en braces,
postcss-selector-parser y source-map-js. Braces no tenía versión corregida;
se elimina esa cadena actualizando Tailwind a 4.3.3 y usando el plugin oficial
`@tailwindcss/vite`. Se retiran PostCSS/Autoprefixer como dependencias directas y
su configuración anterior. El lockfile actualiza source-map-js a su versión
corregida. No se omiten avisos ni se aplica `audit fix --force`.

Se carga explícitamente el tema existente con `@config`, se mantienen los
defaults anteriores de bordes/foco y se adaptan sombras y desenfoques renombrados.
La interfaz se revisa en navegador después de reiniciar Vite; Tailwind 4 requiere
navegadores modernos. Referencias primarias:
[migración oficial](https://tailwindcss.com/docs/upgrade-guide),
[braces](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) y
[source-map-js](https://github.com/advisories/GHSA-68fv-2mgg-jv7q).

Las auditorías npm y pip-audit se ejecutan además del ensayo local completo. Sus
resultados quedan en `.local/verification/`, fuera de Git. Consultan metadatos
públicos de dependencias; no envían perfiles ni activan servicios de empleo.

La auditoría ampliada al entorno Python instalado detectó también herramientas
antiguas y paquetes de una instalación previa. Se actualizan pytest a 9.0.3,
urllib3 a 2.8.0 y pip local a 26.2. Se retiran python-jose y ecdsa de la `.venv`
tras comprobar que no los importa el proyecto y que ningún otro paquete los
necesita; la autenticación ya utiliza PyJWT. Se comprueba `pip check` y se repite
la suite sobre el entorno corregido. La auditoría del entorno instalado incluye
las dependencias del modelo CPU y las herramientas de desarrollo.
### Bloque 32 — Simplificación de capacidades y seguridad por rol

Se retiran las rutas HTTP y de navegación de análisis de proyectos y salas de entrevista. No se borran datos históricos ni se modifica el esquema. La preparación local deja de crear salas y archivos ZIP de demostración. La privacidad de evidencias e intereses se restringe a candidatos. El autenticador incorpora un QR generado en el navegador y una entrada de seis dígitos con instrucciones.

Validación: 38 pruebas dirigidas de retiro y compatibilidad de adaptadores; pruebas de seguridad de cuenta aprobadas; ESLint y Ruff sin errores. El recorrido de aceptación mantiene el avance a entrevista sin la sala integrada.

### Bloque 33 — Aprendizaje por perfil y retos guiados

Catálogo por profesión, sector y habilidades, con diez áreas y exploración manual. Nueve bancos nuevos de cinco decisiones amplían las seis pruebas técnicas; cada intento conserva límites, evaluación en servidor y vigencia. La interfaz muestra una decisión por paso, progreso, revisión final y borrador por cuenta e intento en la pestaña. SQL queda como práctica especializada opcional, con pasos, columnas esperadas y pistas.

Los planes y resultados se reúnen en Mi desarrollo. Administración puede categorizar nuevos recursos. Se añaden enlaces directos revisados a HubSpot Academy y Microsoft Learn, sin compras, afiliación ni descargas automáticas.

Validación: pruebas parametrizadas de cada banco y acreditación, filtros por perfiles de varias profesiones, catálogo administrable, límites y respuestas estrictas. Frontend: ESLint y compilación aprobados.
### Bloque 34 — Evidencias, formación e intereses dentro del flujo existente

Evidencias en Mi perfil, con incorporación explícita de habilidades declaradas y recálculo del índice; nunca se marca verificación por aportar enlaces. Recomendaciones muestra formación ligada a brechas, respaldo por requisito y preferencias de búsqueda. Guardar u ocultar ofertas se integra en recomendaciones y exploración; búsqueda por varios términos, filtros de guardadas/ocultas, paginación y restauración reemplazan el selector masivo. Las rutas antiguas redirigen y se elimina el código frontend de análisis y salas.

Validación: prueba de impacto real de evidencia, conservación de habilidades al retirar una referencia, autorización de privacidad por rol, búsqueda y recuperación entre 350 vacantes; 21 pruebas frontend y ESLint aprobados.

### Bloque 35 — Espacio empresarial, equipo y calidad de ofertas

Acceso empresarial con composición propia, centro de contratación persistente y navegación agrupada. Verificación, integrantes y procesos asignados se reúnen en Organización y equipo: permisos explicados, búsqueda de vacantes, asignaciones por título, estado de invitaciones y cancelación con caducidad del enlace. El entrevistador consulta únicamente procesos asignados, sin avanzar estados. Seguridad no muestra consentimientos de candidato.

Calidad de ofertas incorpora ocho comprobaciones orientativas y edición de los campos que las resuelven, incluidos requisitos ponderados. Se retira la creación y modificación de escenarios de trabajo, conservando registros antiguos. Los selectores muestran títulos y estados, sin identificadores globales. No se renumeran ni eliminan vacantes existentes.

Validación: ocho pruebas dirigidas de organización, calidad e impacto de evidencias; Ruff, ESLint y 21 pruebas frontend aprobados. Revisión visual con cuentas QA ficticias, incluyendo guardado y recálculo de una oferta comercial.

### Bloque 36 — Coherencia y aceptación del rediseño

El texto del matching usa los mismos requisitos ponderados que el índice, con nueva versión de caché. Comunicación como habilidad transversal no desvía por sí sola un perfil comercial hacia diseño. Se conserva la selección de compatibilidad mínima de 0%, se aclaran filtros vacíos y el reto desplaza la vista hasta la decisión activa. El enlace a práctica SQL abre su panel. Se elimina la pantalla antigua de intereses y se actualiza el inventario funcional.

Aceptación local con cuentas QA ficticias independientes: vacante comercial, curso pertinente y plan, guardar/ocultar/restaurar desde la tarjeta, evidencia declarada con impacto explícito, reto por pasos, organización/equipo y separación por rol. Los resultados de la batería completa y del ensayo PostgreSQL quedan en los informes privados habituales; las capturas del rediseño usan el prefijo redesign. No se activan proveedores ni se modifican credenciales de las cuentas previas.


### Bloque 37 — Portales de acceso y registro multipaso

Candidato y empresa usan endpoints propios de login y registro. El servidor fuerza el rol de la ruta incluso si se manipula el payload; la comprobación precede MFA y emisión de tokens o cookies. Los endpoints genéricos históricos permanecen para compatibilidad de integraciones y aceptan un portal explícito. La aplicación siempre usa las rutas por rol. Los registros se separan en cuenta, perfil/organización, seguridad y confirmación; el cambio de portal desmonta el formulario. MFA es un paso independiente para los tres roles. Empresa estrena identidad visual violeta y acceso propio.

### Bloque 38 — Navegación e intereses dentro de la búsqueda

Los tres roles tienen secciones de navegación e iconos distintos para sus funcionalidades. Preferencias y decisiones guardadas se reúnen en un panel con dos vistas. El filtro de condiciones imprescindibles excluye incumplimientos conocidos; datos desconocidos siguen visibles. El índice de compatibilidad permanece independiente. Búsqueda, guardadas, restauración de ocultas y paginación se conservan.

### Bloque 39 — Desarrollo con entregas y progreso

La migración 0037 añade progress y version a learning_plans sin modificar registros anteriores. Las prácticas contienen caso, resultado, tres consignas por sector y revisión final. PATCH /learning/plans/{resource_id}/journey guarda borradores y publica muestras de trabajo en la evidencia del propio perfil. La actualización comprueba versión mediante CAS en el repositorio y devuelve 409 ante cambios concurrentes. Publicar exige desarrollar los tres pasos, reemplaza su evidencia anterior sin duplicarla y permite incorporar habilidades declaradas solo con permiso explícito. No acredita evaluaciones ni crea certificaciones. Los cursos externos siguen requiriendo su formación real y evaluación independiente.

El catálogo retira visualmente recursos guardados y el panel por vacante indica En mi plan. Planes activos y finalizados se distinguen; los resultados muestran evidencias publicadas y evaluaciones con vigencia. Se conservan los planes antiguos marcados manualmente, identificados sin trabajo publicado.

### Bloque 40 — Revisión con varios perfiles y empresas

backend/scripts/seed_review.py solo admite la SQLite aislada, preserva cuentas y claves existentes, y crea cuatro candidatos, tres empresas ficticias con seis ofertas y un administrador local. Las nuevas organizaciones se marcan como verificadas exclusivamente en esta fixture de revisión. No es una validación de identidad real. Las cuentas de empresa/admin requieren configurar el autenticador en el primer acceso. Credenciales privadas, no versionadas: .local/review-accounts.json.

Se añaden pruebas de rechazo cruzado antes de MFA, registro manipulado, publicación y borradores en las diez áreas, propiedad del plan, conflictos de versión, evidencia idempotente y ausencia de acreditación automática. La aceptación de tres empresas usa sesiones independientes, MFA real, vacantes de distintos sectores y deniega editar vacantes ajenas. La interfaz se revisa en escritorio/móvil, temas claro/oscuro, registro, MFA, catálogo, plan y evidencia. Los informes privados contienen resultados sin contraseñas.

La revisión de varias cuentas también separa los filtros de recomendaciones por usuario en el navegador. Inicio y recomendaciones comparten la lectura del porcentaje mínimo, incluido 0%, sin heredar la selección de otra cuenta.


### Bloque 41 — Perfil, extracción y descarga de CV

Bienvenida se distribuye en formulario y vista previa, con autocompletado accesible
por teclado para cargo y ciudad y separadores de miles en COP. El extractor fusiona
fuentes nativas y por coordenadas, recupera responsabilidades por experiencia y
filtra secciones contaminadas. GET /profiles/me/export descarga un PDF privado,
paginado y generado localmente con pypdf, conservando acentos, texto y paleta.
La vista previa permite seleccionar diseño y color antes de guardar. No incluye
fotografía en la descarga ni pretende reproducir exactamente el HTML.

### Bloque 42 — Acceso, seguridad y administración

COMPANY_MFA_REQUIRED conserva true por defecto. Solo .local/backend.env usa false
para la revisión solicitada; tests y ensayo PostgreSQL fuerzan true y verifican
además el modo opcional. Administración sigue requiriendo MFA. Un autenticador
empresarial ya activado nunca se omite. Para restaurar la obligatoriedad local,
cambiar la variable a true y reiniciar el backend; recargar la aplicación.

Seguridad tiene indicadores, anclas y secciones por rol. El acceso administrativo
comparte la composición de marca con contenido propio. Verificación muestra
correo/solicitud, filtros y decisiones confirmadas. Oferta/demanda elimina el
recorte a cuarenta habilidades y pagina la presentación, con búsqueda y orden.
El catálogo educativo integra filtros y tarjetas. Un proveedor de feedback global
muestra resultados temporales al pie de la ventana y ofrece confirmaciones con
foco, Escape y retorno al control. El historial muestra cargo/empresa, no IDs.

### Bloque 43 — Laboratorios y planes acotados

Hasta tres planes activos por usuario, protegido en servidor con bloqueo del
propietario. El abandono usa versión y permisos; conserva evidencias y pruebas.
Los planes históricos que superan el límite se conservan y no aceptan más altas
hasta liberar espacio. Los laboratorios nuevos usan casos específicos en diez
áreas y seis proyectos de tecnología; orden, cálculo y relaciones se evalúan
contra respuestas del servidor. Borradores con versión, explicaciones por paso y
publicación asistida sin agregar habilidades automáticamente. Los trabajos de
texto antiguos publicados mantienen su editor.

Diez bancos nuevos mezclan cinco actividades de distintos formatos. Se validan
tipos, finitud y permutaciones antes de consumir el intento. Los errores ofrecen
explicaciones y recursos por habilidad, incluso al aprobar con 80%. Mis resultados
permite volver a leerlos. Salir conserva respuestas en sessionStorage y no detiene
el tiempo; el intento sigue recuperable durante su vigencia. SQL restringido
continúa disponible como práctica especializada.


SQL mantiene tablas sintéticas, lectura exclusiva, funciones permitidas y límites
de resultados/VM. El presupuesto distingue 0,2 segundos de CPU del hilo y un
máximo de un segundo de reloj; una pausa del planificador no consume CPU. Una
regresión comprueba tanto las consultas válidas bajo pausa como el corte de reloj.


### Bloques 44 y 45 — Diseño por rol, perfiles y demostración

GET /profiles/candidates/{id}?job_id={job_id} permite a la empresa propietaria
revisar una ficha anónima de su postulación. La respuesta usa una lista explícita
de campos profesionales y omite contacto, CV, foto, texto libre y organizaciones.
El contexto de otra vacante visible no revela la identidad en un proceso anónimo.
Las rutas sin contexto conservan sus permisos anteriores. test_hiring cubre la
omisión de identificadores y el acceso por propietario y etapa.

El feedback distingue escrituras de lecturas y del POST de cálculo de match.
Administración organiza motor, integraciones y experimentos por pestañas; el
catálogo conserva los campos entre sus tres pasos y exige publicación explícita.
Recomendaciones enlaza a preferencias en perfil y despliega detalles de respaldo;
la formación usa tarjetas compactas. Retos y cursos tienen vistas separadas.

Para ampliar los ejemplos: backend/.venv/Scripts/python.exe scripts/local.py seed-demo.
El comando solo admite .local/talentsync.sqlite3 en development, crea una copia
SQLite anterior a la primera carga, preserva claves existentes y no duplica las
seis empresas, dieciocho candidatos, veinticuatro vacantes ni treinta y seis
postulaciones. Las cuentas y claves permanecen en .local/review-accounts.json y
.local/ACCESOS_REVISION.md, fuera de Git. Los ejemplos no entrenan el modelo.


### Ajuste local del flujo empresarial — 16 de octubre de 2026

Buscar talento reúne la selección de vacante en un único autocompletado, las
tarjetas y la comparación de cinco perfiles obtenida de la misma respuesta
paginada. El mínimo se recuerda por usuario y admite 60, 70, 80, 90 y 100%; las
postulaciones se muestran sin umbral. Los enlaces antiguos de candidatos
redirigen a esta vista sin iniciar otra consulta de ranking.

El formulario guiado incluye formación y preguntas de preselección, conserva
las valoraciones privadas al editar y usa el catálogo DIVIPOLA para ciudades
presenciales/híbridas. La API rechaza ciudades inexistentes al publicar, incluso
por el formulario antiguo; remoto conserva el territorio permitido en texto.

La publicación requiere 70/100, cargo, salario, contrato, ubicación/modalidad,
responsabilidades, conocimientos/nivel/experiencia (se acepta 0), al menos una
habilidad y plazo de respuesta. Misiones, horario, entrevistas, duración total,
formación y preguntas son opcionales. Las contradicciones críticas continúan
bloqueando. Un cargo de una palabra es válido. El texto de experiencia se
representa con listas y párrafos también en la vista empresarial.
