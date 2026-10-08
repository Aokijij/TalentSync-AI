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
| 2 | Correo local, recuperación, verificación, sesiones, MFA y privacidad | Implementado y probado; SSO externo desactivado y pendiente |
| 3 | Verificación empresarial, equipos y permisos | Implementado: revisión manual local, borradores, invitaciones y permisos en API |
| 4 | Requisitos, evidencias, preferencias y matching avanzado | Implementado; método lexical activo y adaptador neuronal opcional en bloque 10 |
| 5 | Historial de etapas, plazos, avisos y feedback | Implementado: plazos, worker local, cierre idempotente e historial |
| 6 | Brechas, recursos, planes, evaluaciones, pasaporte y portafolio | Implementado con catálogo de proyectos y evaluaciones locales de fundamentos |
| 7 | Selección ciega, calidad de vacantes y contratación por potencial | Implementado: identidad protegida, reglas locales y escenarios laborales |
| 8 | Reputación, incidencias, auditoría y tendencias | Implementado y probado con métricas internas y revisión de incidencias |
| 9 | Entrevistas y colaboración | Implementado: editor, pizarra, versiones y señalización WebRTC local |
| 10 | Personalización, evaluación de modelos e integraciones | Implementado localmente; estado y dependencias externas documentados |

## Comprobaciones

```powershell
backend/.venv/Scripts/python.exe scripts/local.py test
# Desde frontend/: npm test; npm run lint; npm run build
```

El flujo de eventos acepta únicamente metadatos escalares permitidos. No contiene
contraseñas, tokens, CV completos ni respuestas privadas de entrevistas. Cada evento
se guarda en la misma transacción de la operación que describe.

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

Los botones sociales aparecen desactivados: todavía no hay adaptadores OAuth.
Su implementación y vinculación segura quedan pendientes; añadir credenciales
por sí solo no los habilita. El panel del bloque 10 muestra esta limitación.

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
local y se identifica como lexical-hashing-v1. No se presenta como un modelo
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

El método instalado continúa siendo `lexical-hashing-v1`. Hay un adaptador opcional
para un Sentence Transformer ya disponible en disco. No se instalaron sus dependencias
ni se descargaron pesos, y no se probó inferencia con un modelo real. Las pruebas
comprueban que no admite nombres remotos ni formatos ejecutables.

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

El panel muestra explícitamente integraciones pendientes: LinkedIn y SSO
corporativo, extracción automática de GitHub, catálogos educativos, afiliación,
validación contra registros oficiales, servidor TURN y ejecutor de código aislado.
Requieren adaptadores/configuración o acuerdos reales; no basta con pegar claves.
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
detiene y solicita el método original: no vincula cuentas automáticamente. Vincular
proveedores a una cuenta existente sigue pendiente de un flujo de reautenticación.
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
