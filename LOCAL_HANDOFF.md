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
