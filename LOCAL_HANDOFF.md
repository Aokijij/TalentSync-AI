# Cierre del desarrollo local

Estado revisado el **8 de octubre de 2026**. La versión local conserva el stack
del proyecto: FastAPI, React, SQLAlchemy y Alembic. No se desplegó ni se hizo push.
Los bloques están en `codex/desarrollo-funcionalidades-local`; el inventario por
rol está en [FEATURES_LOCAL.md](FEATURES_LOCAL.md) y el detalle técnico en
[DEVELOPMENT.md](DEVELOPMENT.md).

## Qué queda terminado y comprobable en esta máquina

| Área solicitada | Resultado local |
| --- | --- |
| Login y registro por rol | Portales que rechazan cuentas de otro rol desde el servidor; registros separados de cuatro pasos, revisión final y pantalla propia de MFA. Sesiones revocables, CSRF, QR local y sin registro público de administradores. |
| Acceso social y corporativo | Adaptadores Google, GitHub, LinkedIn, Workspace y Entra ID; estados, PKCE, firmas, identidades aprovisionadas y MFA probados con proveedores en memoria. Desactivados sin configuración real. |
| Compatibilidad avanzada | Habilidades normalizadas, requisitos ponderados, relaciones dirigidas entre habilidades, preferencias bidireccionales y explicaciones. MiniLM multilingüe activo en CPU, con inferencia offline. |
| Personalización y MLOps | Consentimiento, señales de interés, retirada de datos, señal colaborativa con umbral de muestra, evaluación separada y mantenimiento condicionado a datos suficientes. Los datos ficticios no entrenan modelos de contratación. |
| Anti-ghosting | Historial, plazos, recordatorios, cierre idempotente y feedback explícitamente separado de motivos reales del reclutador. |
| Micro-upskilling | Brechas por vacante, catálogo visual, planes con casos por sector, borrador persistente y entrega que añade una evidencia declarada al perfil. Proyección hipotética y evaluaciones independientes. |
| Evaluación y Zero-CV | Quince micropruebas guiadas, catálogo por perfil en diez áreas, cuatro retos SQL restringidos opcionales y pasaporte con alcance/caducidad. Evidencias en Mi perfil con impacto declarado explícito en compatibilidad. |
| Empresa y selección | Espacio empresarial distinto, revisión manual, equipos y asignaciones por nombre de vacante, invitaciones cancelables, selección ciega, revelación controlada y calidad editable de ofertas. |
| Simplificación | Retirados análisis de proyectos, salas, pizarra y nuevos escenarios laborales. Historial conservado. Compatibilidad, formación e intereses integrados en recomendaciones; requisitos dentro de Calidad de ofertas. |
| Administración | Incidencias privadas y revisión, reputación, tendencias internas, auditoría de matching, modelos y catálogo educativo con patrocinio visible. |

La aceptación completa conecta candidato, empresa y administrador con sesiones
independientes y MFA: desde registro/verificación hasta publicación, postulación,
práctica SQL, avance a la etapa de entrevista, cierre por plazo, revisión de incidencia y logout.
Se ejecuta sobre una base temporal y no modifica tus cuentas locales.

## Cómo repetir la validación

Desde la raíz del proyecto:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py doctor
backend/.venv/Scripts/python.exe scripts/local.py verify
backend/.venv/Scripts/python.exe scripts/local.py rehearse
```

`doctor` comprueba runtimes, dependencias frontend, aislamiento de configuración,
integridad y última migración de la SQLite local, presencia de pesos y respuestas
HTTP de los servidores. No conecta a PostgreSQL, cambia filas ni muestra claves.
Que los servidores estén detenidos produce un aviso; no impide ejecutar las
pruebas aisladas. Configuración inválida, migración atrasada o pesos configurados
ausentes sí se identifican como faltantes.

`verify` ejecuta comprobación de dependencias Python, lint, todas las pruebas
backend/frontend, compilación Vite y, si está configurado, el modelo neuronal
real en modo offline. Se detiene en el primer fallo y devuelve un código de error.
La prueba del modelo utiliza la ruta realmente configurada. No descarga pesos,
activa integraciones ni despliega. Registra una huella del código y rechaza el
resultado si los archivos cambian durante las comprobaciones.

Los informes se guardan en `.local/verification/doctor.json` y `validation.json`,
sin credenciales, tokens ni contenido de perfiles. `.local/` está excluido de Git.
El runner habitual comprueba subida/bajada en SQLite y SQL de PostgreSQL
offline; no equivale por sí mismo a una ejecución contra PostgreSQL real.
En la siguiente etapa, el bloque 25 añade un ensayo independiente contra
PostgreSQL 18 real con aceptación entre roles y restauración exacta de sus 27
tablas: `scripts/staging_postgres.py check`. No reemplaza ni modifica esta SQLite.
Los comandos, límites y preparación externa están en
[infra/staging/README.md](infra/staging/README.md).

La migración local vigente es 0037. SMTP está preparado con cola/reintentos y
pruebas simuladas y conexiones SSL/STARTTLS reales a un sumidero local, pero
permanece desactivado. El presupuesto autorizado es cero:
no se crea infraestructura Azure ni se contratan proveedores.

`rehearse` reúne la validación completa, el ensayo PostgreSQL y el diagnóstico,
exige la misma huella de código y guarda `rehearsal.json`. También genera
`capacity.json` (ocho candidatos simultáneos, 50 ofertas, sesiones/CSRF y escrituras
aisladas) y `matching-regressions.json` (matriz sintética con 16 variantes de
identidad). La capacidad mide ASGI en proceso y matching léxico con limitador
desactivado; no certifica rendimiento en producción ni equidad demográfica.

Las auditorías adicionales se repiten con `npm audit --audit-level=high` desde
`frontend/` y `python -m pip_audit -r requirements-lite.txt --progress-spinner off`
desde `backend/` (requiere pip-audit instalado). Consultan avisos públicos en
Internet; no activan proveedores de la plataforma ni generan cargos. El bloque
31 migra Tailwind a 4.3.3 para eliminar dependencias vulnerables de construcción.
La auditoría ampliada `python -m pip_audit --local --progress-spinner off` examina
también el modelo CPU y herramientas instaladas. Se recomienda pip 26.2 o
posterior; pytest y urllib3 corregidos están fijados en los requisitos.

Para arrancar: `scripts/local.py backend` y, desde `frontend/`,
`npm run dev -- --host 127.0.0.1`. La aplicación está en
`http://127.0.0.1:5173`. `scripts/local.py accounts` muestra los accesos ficticios
solo en tu terminal. Los archivos `.env` originales siguen sin modificarse.

## Qué requiere la siguiente etapa

| Dependencia externa | Preparación existente | Lo necesario para activarla y comprobarla |
| --- | --- | --- |
| Google/GitHub/LinkedIn | Adaptadores y pruebas del flujo, vinculación y revocación | Registrar aplicaciones, configurar credenciales/callbacks y usar cuentas reales de prueba. LinkedIn necesita HTTPS. |
| Workspace/Entra ID | SSO administrativo, aprovisionamiento por identidad, MFA y política opcional | Aplicación y organización reales; vincular administradores existentes. No activar la política obligatoria antes de comprobar el acceso completo. |
| Cursos y afiliación | Catálogo local, importación JSON y transparencia comercial | Acceso/API o catálogo autorizado y acuerdos comerciales. No se han integrado APIs específicas de Coursera, Udemy, Platzi o SENA ni cobros reales. |
| Verificación legal | Solicitud, cola de revisión y decisiones manuales | Proveedor o registro oficial y criterios operativos de verificación. |
| Salarios del mercado | Alertas por reglas y referencias de la base local | Fuente salarial autorizada, actualización, cobertura y validación por región/rol. |
| Ejecución general de código | SQL real restringido opcional para perfiles de tecnología | Ejecutor con aislamiento de procesos/red/archivos y límites de recursos. No se encontró Docker/Podman en PATH; ejecutar código arbitrario en el proceso del backend no forma parte de esta versión. |
| Predicción y equidad | Métricas internas, auditoría de invariancia y herramientas de evaluación | Datos reales suficientes y consentidos, evaluación representativa y supervisión. El match actual es afinidad, no probabilidad de contratación ni garantía de ausencia de sesgo. |
| Infraestructura | Aplicación y APIs compatibles con configuración externa | Hosting, PostgreSQL real, dominio/HTTPS, correo real, secretos, backups operativos, observabilidad, red/VPN y validación de despliegue. |

No hace falta cambiar de stack ni dividir la aplicación en microservicios para
probar esta versión local. La separación física de servicios y su operación
corresponden al diseño de infraestructura de la siguiente etapa.


## Cuentas adicionales para revisar los cambios

La fixture de revisión es independiente de tus cuentas previas. Sus ocho accesos
están en `.local/review-accounts.json`, excluido de Git. Cuatro candidatos cubren
ventas, finanzas, logística y atención administrativa en salud; las tres empresas
son Comercio Aurora, Ruta Clara y Bienestar Horizonte, todas ficticias. Cada una
tiene dos vacantes de prueba y hay un administrador adicional.

Los candidatos entran en `/login`, las empresas en `/empresa/login` y el
administrador en `/acceso-administracion`. Administración configura MFA en su
primer ingreso desde Seguridad, escaneando el QR. Para esta revisión local el alta
de MFA empresarial es opcional; los autenticadores existentes siguen activos. No se entrega un código TOTP
fijo porque cambia con el tiempo. Guarda los códigos de recuperación al activar
el autenticador. Los accesos sociales continúan desactivados sin proveedor real.

Para preparar o comprobar estas fixtures sin duplicarlas: `backend/.venv/Scripts/python.exe scripts/local.py seed-review`. Este comando no restablece contraseñas ni reinicia avances.


La revisión de usabilidad añade laboratorios guiados, límite de tres planes activos,
confirmaciones y avisos flotantes. Las capturas privadas usan el prefijo usability.
El CV debe volver a cargarse para aplicar el extractor corregido. Si una extensión
del navegador superpone su panel sobre el lado derecho, debe cerrarse ese panel;
la aplicación no altera la extensión ni intenta cubrirla con otro z-index.


## Segunda revisión visual

Los accesos originales de revisión siguen vigentes. La ampliación añade seis
empresas de tecnología, finanzas, logística, atención administrativa en salud,
educación y diseño; cada una tiene cuatro ofertas ficticias y tres candidatos
con perfiles desarrollados. Hay 24 accesos nuevos y 36 postulaciones adicionales.
Consulta .local/ACCESOS_REVISION.md para elegir un rol. seed-demo puede repetirse
sin duplicar registros ni cambiar contraseñas; vacancy ID 4 se conserva.

En selección anónima se puede abrir Ver perfil anónimo; la ficha omite identidad
hasta la etapa de entrevista. Las ofertas nuevas incluyen procesos con y sin
selección anónima para revisar ambas variantes.

Motor e integraciones tiene tres pestañas y color ámbar de administración. El
catálogo guía la creación de recursos externos con validación, vista previa y
confirmación final. Los ejercicios internos ya pertenecen a la biblioteca.
En candidato, Guardadas y Ocultas están en Explorar vacantes; las preferencias
están en Mi perfil y Mi desarrollo separa retos de cursos. Los avisos de guardado
se muestran únicamente tras escrituras reales y se limpian al cambiar de vista.
Las capturas privadas de esta revisión usan el prefijo design en .local/verification.

## Revisión de mapa, preferencias y escalado visual

Se recuperó el radar de habilidades en Recomendaciones. Las condiciones provienen
de los campos existentes de Mi perfil; las marcas de imprescindible se gestionan
en Compatibilidad y formación. El formulario duplicado fue retirado.
Explorar vacantes conserva un solo interruptor de personalización y las colecciones
Todas, Guardadas y Ocultas. Mi desarrollo usa una barra de navegación con iconos.

El error de etapas provenía de vacantes antiguas sin pipeline_stages: el cliente
mostraba etapas predeterminadas y el servidor rechazaba guardarlas. El dominio
ahora aplica el mismo proceso estándar al validar y titular esas etapas, sin
modificar procesos personalizados ni datos originales. La regresión prueba el
movimiento, el acceso a identidad después de entrevista y la protección de versión.

Verificación está paginada de cinco en cinco; el directorio del ecosistema, de seis
en seis, muestra métricas completas al abrir una empresa. La búsqueda abarca todos
los resultados recibidos. Las capturas y el escenario ficticio de comprobación
usan el prefijo refinement en .local/verification. No se cambiaron contraseñas.

## Escenarios funcionales por rol

La carga `scripts/local.py seed-scenarios` añade 26 cuentas independientes para
recorrer candidato, empresa, equipo y administración. La matriz pública está
en `ESCENARIOS_FUNCIONALES.md`; los accesos privados y pasos concretos están en
`.local/escenarios/GUIA_ESCENARIOS.md`. Es aditiva, idempotente y solo admite la
SQLite aislada. No restablece contraseñas ni los recorridos ya probados.


## Revisión por roles y uso local (9 de octubre de 2026)

- Resultados con tarjetas de puntuación, vigencia, tipo de evaluación y siguientes pasos; detalle de cada curso/práctica con temario y aporte al perfil.
- Certificado externo: finalizar el plan habilita un formulario que exige declaración de posesión y enlace HTTPS público al certificado/verificación. Se guarda en Certificaciones y Evidencias como aportado, sin marcar verificado ni añadir habilidades automáticamente.
- Condiciones imprescindibles al inicio de Recomendaciones, basadas en el perfil; formación sin brechas con estado informativo y acciones a Plan y Resultados.
- Incidencias con empresa, vacante, respuesta compartida y seguimiento. El reporte original sigue reservado al reportante y al administrador.
- Verificación con identidad tributaria, actividad, sede, representación, contacto, registro, soporte y declaración; revisión administrativa manual. Las solicitudes incompletas no pueden aprobarse. Una empresa suspendida puede actualizar soportes sin recuperar permisos automáticamente.
- Entrevistador: búsqueda de asignaciones, alias de selección ciega, contexto de la entrevista y evaluación privada. No cambia decisiones de contratación. Las notas viven en el proceso, fuera del registro de auditoría.
- Acceso retirado: aviso claro y solicitud de revisión al propietario, una cada 24 horas. El aviso no restablece permisos.
- Regreso desde perfil a la vacante seleccionada del tablero. Calidad de ofertas con criterios ponderados, prioridades y ejemplos de corrección.
- MFA de administración: `LOCAL_ADMIN_REVIEW_ENABLED=true` solo funciona con desarrollo y SQLite. Se conserva el autenticador existente. En producción, staging o PostgreSQL la política permanece activa. Las pruebas restablecen la opción a false.
- Pausa temporal para todos los roles: `LOCAL_MFA_REVIEW_ENABLED=true` en `.local/backend.env` omite los desafíos y la configuración obligatoria de MFA en desarrollo con SQLite, también para autenticadores ya inscritos y accesos sociales. No borra secretos, recuperaciones ni permisos. Para reactivar la política, cambiar a false y reiniciar el backend; las sesiones abiertas sin MFA deberán autenticarse de nuevo. Las pruebas siempre desactivan esta pausa.
- Migración `0038_interview_evaluations`: agrega la columna de notas de entrevista, sin modificar las postulaciones existentes.

El entorno local guarda archivos, correo de demostración y base SQLite en `.local/`; las llamadas de Azure, correo SMTP y portales de pago permanecen deshabilitadas por `scripts/local.py`. Para arrancar: `backend/.venv/Scripts/python.exe -X utf8 scripts/local.py backend` y el servidor Vite de `frontend`. Cuentas y recorridos: `.local/escenarios/GUIA_ESCENARIOS.md` (privado, no versionado). La revisión de gastos y el alcance propuesto para retirar Azure están en `.local/AZURE_USO_LOCAL.md`.


## Cierre adicional de funciones locales

La paginación completa de verificación, directorio empresarial y equipo, la
integración de calidad en el orden de recomendaciones, los borradores de
redacción y los estados efectivos de integraciones se describen en
[docs/CIERRE_FUNCIONES_LOCALES.md](docs/CIERRE_FUNCIONES_LOCALES.md).
La revisión sigue sin proveedores externos ni servicios de pago. Los certificados
y las empresas continúan con comprobación manual, claramente identificada.

## Primera etapa de integraciones

GitHub público ya tiene recorrido de candidato con consentimiento, vista previa
y guardado como evidencia declarada. El entorno local habilita ese lector.
Microsoft Learn incorpora vista previa administrativa e importación de
borradores, pendiente de credenciales de Microsoft Entra. Resend está preparado
como transporte de la bandeja de salida. Se autorizó y Resend aceptó un único
correo de prueba al titular, ejecutado mediante `scripts/resend_test.py`, con
configuración privada en `.local/resend.env`. Repetir el comando no duplica un
envío aceptado. La prueba no procesa la bandeja de salida. El lanzador local
sigue impidiendo correo externo de la aplicación y acceso a almacenamiento de
Azure. Para otros destinatarios falta un dominio/remitente propio verificado.

Activación, límites y estado real en
[docs/INTEGRACIONES_PRIMERA_ETAPA.md](docs/INTEGRACIONES_PRIMERA_ETAPA.md).
Plantilla sin secretos: `backend/integrations.env.example`.

Correo: Resend y SMTP usan una plantilla HTML compartida con alternativa de
texto. Botones solo para enlaces de cuenta/invitación del `PUBLIC_APP_URL`
configurado; contenido escapado y preencabezado sin tokens. Vistas previas sin
credenciales ni envío: `scripts/resend_test.py --preview`. Se conservó el estado
del único correo real aceptado; el nuevo diseño no se reenvió. Pasaron 65 pruebas
de correo/integraciones y lint de los archivos modificados. Propuesta de dominio
pendiente de disponibilidad/compra: `talentsyncempleo.com`; no se configuró DNS.

## Continuación gratuita: Codewars

`CODEWARS_ENABLED=true` en `.local/backend.env`. El candidato puede consultar un
usuario público desde Evidencias, revisar rangos/lenguajes, seleccionar cuáles
relacionar y guardar una referencia sin verificar. Se exige consentimiento y
declaración de titularidad; añadir habilidades al perfil es opcional. Otra
consulta/guardado de la misma cuenta actualiza la referencia sin duplicarla.
La API no autentica titularidad ni acredita competencias profesionales.

Consulta pública sin credenciales; presupuesto de 50 peticiones/hora/proceso,
caché de 32 cuentas/10 minutos, respuesta máxima de 128 KiB. La vista previa
cifrada pertenece al candidato y caduca en 10 minutos. No se guardan nombre,
clan, habilidades autodeclaradas ni soluciones. No hay sincronización automática.
El lanzador conserva correo externo apagado y también desactiva Codewars en
las pruebas automatizadas. Se reinició el backend local con la nueva opción;
la comprobación API confirma GitHub, Codewars, correo local y pausa de MFA.
Validación: 556 pruebas backend aprobadas, una omitida de PostgreSQL staging,
28 pruebas frontend, ruff/eslint y build correctos. Componente nuevo comprobado
mediante API y compilación; revisión visual pendiente por el bloqueo del
navegador descrito en la guía de integraciones. Backend actualizado: Uvicorn
en 127.0.0.1:8000, sesión 33439, PID 19960.

## Evidencias adaptadas a cada profesión

El perfil prioriza el formulario de logros, trabajos y certificados. GitHub y
Codewars están agrupados en una sección opcional, plegada por defecto. Solo se
montan al abrirla por primera vez; plegarla después conserva lo introducido.
El título menciona los proveedores cuando hay profesión/habilidades explícitas
de programación o referencias técnicas guardadas. Para otros perfiles aparece
«Otras fuentes de evidencia». El sector preferido no determina esta selección.
Todo candidato conserva acceso voluntario y todas sus evidencias guardadas;
esta adaptación solo afecta la presentación. Sin cambios de backend, permisos
ni puntuaciones. Validación: 32 pruebas frontend, eslint y build correctos.
La revisión visual continúa pendiente por el bloqueo del navegador indicado
en la guía de integraciones.

## Diseño de evidencias

La sección muestra primero las referencias guardadas en tarjetas, con tipo,
habilidades como etiquetas, enlace y acción de retirar. Descripción completa,
procedencia y límites de verificación se consultan en un detalle desplegable.
El formulario se abre desde «Añadir evidencia», conserva el borrador al cerrar
y se limpia tras guardar. Incluye foco al abrir/cerrar, bloqueo durante guardado,
estados de carga/error y una vista vacía. GitHub/Codewars siguen opcionales al
final. Estilos propios con variables de tema, dos columnas en escritorio y una
en móvil. Sin cambios de API ni datos. Pasaron 32 pruebas frontend, eslint y
compilación; revisión visual pendiente por el bloqueo de navegador existente.

## Biblioteca ampliada de formación · 10 de octubre de 2026

Se añadieron 34 recursos oficiales de 11 proveedores: Microsoft Learn, Google
Career Certificates, Google Skillshop, HubSpot Academy, IBM en Coursera,
Cisco Networking Academy, freeCodeCamp, OpenLearn, AWS, Harvard CS50 y Rutgers
en Coursera. Son 24 de acceso gratuito y 10 de pago, en nueve áreas. La selección
es editorial y versionada, con enlaces revisados; no pretende ser una API de
sincronización de los once proveedores ni el catálogo completo de cada uno.

Cada ficha incluye temario resumido, nivel, idiomas confirmados, requisitos,
condiciones de acceso/certificación, referencia de duración e idea de evidencia
propuesta por TalentSync. Las estimaciones propias se distinguen de duraciones
publicadas. El precio regional se consulta en el proveedor; una prueba temporal
no se anuncia como formación gratuita permanente. La práctica local se presenta
separada del temario externo. Completar el plan no concede credenciales externas.

El candidato dispone de filtros por proveedor, idioma, nivel, coste, origen y
formato, junto con búsqueda, áreas y páginas de doce recursos. «Todas las áreas»
permite explorar la biblioteca completa. El administrador explora fuentes en
páginas de ocho, selecciona cursos y los importa como borradores o los publica
explícitamente. Puede editar sus detalles; el conector API de Learn conserva
su configuración autorizada independiente. Reimportar conserva ediciones,
archivados y planes. Las referencias antiguas duplicadas se conservan archivadas
para resolver planes existentes, sin volver a aparecer como cursos nuevos.

El comando `backend/.venv/Scripts/python.exe scripts/local.py seed-education`
publica la selección solo en `.local/talentsync.sqlite3`, sin sustituir datos,
crear cuentas, comprar cursos o llamar servicios externos. Se ejecutó una vez
creando 34 recursos y una segunda conservando los mismos 34. Evidencia agregada
sin secretos en `.local/verification/education-catalog.json` y `education-api.json`.
Correo externo sigue apagado y la pausa local de MFA se conserva.

Validación: batería completa de 570 pruebas backend aprobadas y una omitida de
PostgreSQL staging; 33 pruebas frontend, ruff, eslint y build correctos. Después
del ajuste final para que importar un borrador no retire una referencia publicada,
pasaron de nuevo 97 pruebas de aprendizaje, integraciones y arquitectura. La API
real confirma los 34 recursos oficiales activos, sin duplicar sus tarjetas, y el
acceso del administrador. Revisión visual pendiente por el bloqueo de navegador
ya documentado. Backend actualizado en 127.0.0.1:8000, sesión 76496, PID 18848.


## Formación en español y lectura de fuentes públicas — 10 de octubre de 2026

La biblioteca editorial contiene **65 recursos de 13 grupos de proveedores**:
55 de acceso gratuito y 10 de pago. Esta ampliación incorpora **19 programas
virtuales del SENA y 12 cursos en español de HP LIFE**. Cubre las diez áreas,
incluida atención y procesos en salud. Los temarios resumidos, requisitos,
certificación e ideas de evidencia están separados de los laboratorios locales.
Los cursos de HP LIFE tienen una reserva de estudio orientativa de 2 horas;
la ficha pública no publica una duración numérica. Sus certificados son de
finalización, sin acreditación educativa oficial.

En Mi desarrollo > Cursos y prácticas hay accesos a Gratis en español y SENA.
Los filtros avanzados incluyen idioma, modalidad, disponibilidad y certificado.
El detalle muestra edad mínima, cobertura, última consulta y condiciones.
Una inscripción anunciada no reserva una plaza. A los 14 días sin comprobación,
o si falla una actualización, la disponibilidad pasa a por confirmar.

Administración > Catálogo educativo permite buscar programas virtuales del
SENA por tema, revisar sus enlaces e importar una selección. Por defecto quedan
como borradores. El mapeo automático de habilidades es una sugerencia por título
que debe revisarse; no acredita conocimientos ni modifica perfiles. La consulta
está limitada a 20 programas y cacheada 24 horas. La importación reconoce un
curso ya incorporado editorialmente y conserva sus ediciones y planes.

Las convocatorias de Sapiencia se muestran en un bloque independiente, paginado
de cuatro en cuatro, con requisitos territoriales y filtro de estado. No se
convierten en cursos ficticios ni se les asignan horas inventadas. El candidato
solo lee la copia guardada en la base local.

Se implementó lectura de las páginas públicas de Betowa y Sapiencia, con hosts
fijos, comprobación de robots.txt, sin redirecciones, límites de tamaño/tiempo,
caché persistente y conservación de la última lectura si falla la fuente. No se
usaron APIs privadas, RSS supuestos, cuentas de alumnos ni contenido de pago.
Si cambia el HTML puede requerirse adaptar el lector. Las fuentes originales:
https://betowa.sena.edu.co/oferta y https://sapiencia.gov.co/convocatorias/.
HP LIFE es una selección editorial: https://www.life-global.org/es/allcourses
con condiciones revisadas en https://www.life-global.org/es/help.

La migración vigente es **0040_learning_sources**. Solo añade una caché pública;
no elimina tablas ni cuentas. Para repetir la carga y actualización local:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py setup
backend/.venv/Scripts/python.exe scripts/local.py seed-education
backend/.venv/Scripts/python.exe scripts/local.py sync-education
```

La actualización diaria se habilitó únicamente en `.local/backend.env` mediante
PUBLIC_LEARNING_REFRESH_ENABLED=true. Se ejecuta al arrancar y cada 24 horas
mientras el backend permanece abierto; si el equipo está apagado se recupera al
siguiente arranque. Solo revisa fichas del SENA ya guardadas y convocatorias de
Sapiencia. No publica nuevos cursos, no sobrescribe contenido editorial y no
consume servicios de pago. Los demás entornos la tienen desactivada por defecto.
Las consultas de candidatos no desencadenan conexiones externas. El refresco se
limita por cantidad, tiempo y fallos consecutivos; no constituye un crawler masivo.

Microsoft Learn mantiene su conector autenticado pendiente de acceso Entra.
YouTube Data API y catálogos comerciales siguen requiriendo configuración o
acceso autorizado; esta ampliación no simula una sincronización con ellos.
