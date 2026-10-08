# Cierre del desarrollo local

Estado revisado el **8 de octubre de 2026**. La versión local conserva el stack
del proyecto: FastAPI, React, SQLAlchemy y Alembic. No se desplegó ni se hizo push.
Los bloques están en `codex/desarrollo-funcionalidades-local`; el inventario por
rol está en [FEATURES_LOCAL.md](FEATURES_LOCAL.md) y el detalle técnico en
[DEVELOPMENT.md](DEVELOPMENT.md).

## Qué queda terminado y comprobable en esta máquina

| Área solicitada | Resultado local |
| --- | --- |
| Login y registro por rol | Sesiones opacas revocables, CSRF, correo de verificación/recuperación en bandeja local, MFA obligatorio para empresa y administrador, sin registro público de administradores. |
| Acceso social y corporativo | Adaptadores Google, GitHub, LinkedIn, Workspace y Entra ID; estados, PKCE, firmas, identidades aprovisionadas y MFA probados con proveedores en memoria. Desactivados sin configuración real. |
| Compatibilidad avanzada | Habilidades normalizadas, requisitos ponderados, relaciones dirigidas entre habilidades, preferencias bidireccionales y explicaciones. MiniLM multilingüe activo en CPU, con inferencia offline. |
| Personalización y MLOps | Consentimiento, señales de interés, retirada de datos, señal colaborativa con umbral de muestra, evaluación separada y mantenimiento condicionado a datos suficientes. Los datos ficticios no entrenan modelos de contratación. |
| Anti-ghosting | Historial, plazos, recordatorios, cierre idempotente y feedback explícitamente separado de motivos reales del reclutador. |
| Micro-upskilling | Brechas por vacante, recursos y proyectos, plan personal, proyección hipotética y número de otras ofertas examinadas. |
| Evaluación y Zero-CV | Micropruebas de fundamentos, dos retos SQL con ejecución restringida real, pasaporte con alcance/caducidad, evidencias y análisis estático optativo de proyectos. |
| Empresa y selección | Revisión empresarial manual, equipos y permisos, selección ciega, revelación controlada, calidad de ofertas y escenarios de trabajo. |
| Entrevistas | Editor y pizarra compartidos, versiones y conflictos, presencia/señalización efímera, acceso por proceso y WebRTC de dos participantes. |
| Administración | Incidencias privadas y revisión, reputación, tendencias internas, auditoría de matching, modelos y catálogo educativo con patrocinio visible. |

La aceptación completa conecta candidato, empresa y administrador con sesiones
independientes y MFA: desde registro/verificación hasta publicación, postulación,
práctica SQL, entrevista, cierre por plazo, revisión de incidencia y logout.
Se ejecuta sobre una base temporal y no modifica tus cuentas locales.

## Cómo repetir la validación

Desde la raíz del proyecto:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py doctor
backend/.venv/Scripts/python.exe scripts/local.py verify
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

La migración local vigente es 0036. SMTP está preparado con cola/reintentos y
pruebas simuladas, pero permanece desactivado. El presupuesto autorizado es cero:
no se crea infraestructura Azure ni se contratan proveedores.

Para arrancar: `scripts/local.py backend` y, desde `frontend/`,
`npm run dev -- --host 127.0.0.1`. La aplicación está en
`http://127.0.0.1:5173`. `scripts/local.py accounts` muestra los accesos ficticios
solo en tu terminal. Los archivos `.env` originales siguen sin modificarse.

## Qué requiere la siguiente etapa

| Dependencia externa | Preparación existente | Lo necesario para activarla y comprobarla |
| --- | --- | --- |
| Google/GitHub/LinkedIn | Adaptadores y pruebas del flujo, vinculación y revocación | Registrar aplicaciones, configurar credenciales/callbacks y usar cuentas reales de prueba. LinkedIn necesita HTTPS. |
| Workspace/Entra ID | SSO administrativo, aprovisionamiento por identidad, MFA y política opcional | Aplicación y organización reales; vincular administradores existentes. No activar la política obligatoria antes de comprobar el acceso completo. |
| Repositorios GitHub | Lectura pública optativa, revisión fija, límites y vista previa | Activar explícitamente el adaptador y obtener consentimiento en cada consulta; validar con repositorios autorizados. |
| Cursos y afiliación | Catálogo local, importación JSON y transparencia comercial | Acceso/API o catálogo autorizado y acuerdos comerciales. No se han integrado APIs específicas de Coursera, Udemy, Platzi o SENA ni cobros reales. |
| Verificación legal | Solicitud, cola de revisión y decisiones manuales | Proveedor o registro oficial y criterios operativos de verificación. |
| Salarios del mercado | Alertas por reglas y referencias de la base local | Fuente salarial autorizada, actualización, cobertura y validación por región/rol. |
| Videollamadas entre redes | Adaptador STUN/TURN con credenciales temporales | Servidor de retransmisión, configuración de red y pruebas audiovisuales entre redes reales. No se activaron cámara ni micrófono durante este cierre. |
| Ejecución general de código | SQL real restringido; editor de entrevista sin ejecución | Ejecutor con aislamiento de procesos/red/archivos y límites de recursos. No se encontró Docker/Podman en PATH; ejecutar código arbitrario en el proceso del backend no forma parte de esta versión. |
| Predicción y equidad | Métricas internas, auditoría de invariancia y herramientas de evaluación | Datos reales suficientes y consentidos, evaluación representativa y supervisión. El match actual es afinidad, no probabilidad de contratación ni garantía de ausencia de sesgo. |
| Infraestructura | Aplicación y APIs compatibles con configuración externa | Hosting, PostgreSQL real, dominio/HTTPS, correo real, secretos, backups operativos, observabilidad, red/VPN y validación de despliegue. |

No hace falta cambiar de stack ni dividir la aplicación en microservicios para
probar esta versión local. La separación física de servicios y su operación
corresponden al diseño de infraestructura de la siguiente etapa.
