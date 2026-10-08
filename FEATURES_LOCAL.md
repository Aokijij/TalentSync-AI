# Funcionalidades de la versión local

Proyecto compatible con su stack existente: FastAPI, React y SQLAlchemy.
Rama `codex/desarrollo-funcionalidades-local`, bloques 1–36.
No se realizó despliegue ni push. Los datos de demostración son ficticios y la
base aislada vive en `.local/talentsync.sqlite3`.

## Candidato

| Funcionalidad | Implementación y dónde usarla |
| --- | --- |
| Registro y bienvenida | Correo/contraseña, verificación mediante bandeja local y bienvenida para completar perfil y preferencias. |
| Acceso social | Adaptadores Google, GitHub y LinkedIn; vinculación y retirada con reautenticación, MFA cuando corresponde y control de sesión. Desactivados sin configuración real. |
| Acceso persistente y recuperable | Sesiones opacas revocables, recordar dispositivo personal, recuperar acceso, cambiar correo y segundo factor opcional. `/seguridad`. |
| Compatibilidad bidireccional | Habilidades, contexto semántico, formación, certificados, idiomas y preferencias de salario, modalidad y ubicación. Preferencias en `/recomendaciones`; requisitos comparables en `/empresa/calidad`. |
| Explicaciones de compatibilidad | Componentes ponderados, requisitos esenciales, datos ausentes, brechas y bases relacionadas. La relación entre habilidades no acredita dominio. |
| Semántica multilingüe | Modelo MiniLM activo en CPU, con pesos locales verificados y sin inferencia remota. El porcentaje es un índice de afinidad. |
| Seguimiento de procesos | Etapas, historial, plazos, notificaciones y cierre automático por falta de respuesta; feedback basado en datos registrados, separado de la razón real del reclutador. `/procesos/{id}`. |
| Aprendizaje dirigido | Brecha por vacante, recursos asociados, estimación hipotética de mejora por hora y otras vacantes examinadas, excluyendo la seleccionada. Dentro del detalle de compatibilidad de `/recomendaciones`. |
| Plan de práctica | Guardar recursos, marcar progreso y conservar planes aunque se archive un recurso. Completar el plan no acredita la habilidad. |
| Brechas recurrentes | Patrones de habilidades pendientes en procesos finalizados, sin atribuir automáticamente el rechazo a esa brecha. |
| Micropruebas | Quince evaluaciones de cinco decisiones con recorrido por pasos, progreso y revisión final. Catálogo de diez áreas según profesión, sector y habilidades; incluye ventas, atención, administración, finanzas, logística, educación, diseño y procesos de salud no clínicos, además de tecnología y competencias transversales. |
| Retos SQL reales | Cuatro retos originales: totales pagados, clientes sin pagos, totales/promedios y último pedido; vista previa y entrega contra tres conjuntos sintéticos, en SQLite aislada y restringida. |
| Pasaporte de habilidades | Resultados, versión, alcance y caducidad. Aprobaciones de fundamentos integradas con el perfil. |
| Evidencias de experiencia | Logros, muestras de trabajo, certificaciones o referencias en `/perfil#evidencias`. Incorporación explícita de habilidades declaradas al perfil para recalcular compatibilidad; respaldo visible por requisito. No descarga archivos ni atribuye verificación automática. |
| Personalización consentida | Intereses, ofertas ocultas, recuperación de decisiones y señal colaborativa agregada con mínimo de vecinos. Botones en cada oferta, filtros de guardadas/ocultas, búsqueda por varios términos, paginación y recuperación en `/vacantes` y `/recomendaciones`. |
| Privacidad | Consentimientos independientes para personalización, evidencia y avisos de nuevas habilidades; retirada de señales y artefactos aprendidos asociados. `/seguridad`. |

## Empresa

| Funcionalidad | Implementación y dónde usarla |
| --- | --- |
| Registro empresarial y revisión | Verificación de correo, organización pendiente y revisión administrativa local. Publicación condicionada a aprobación. |
| Equipo y permisos | Propietario, reclutador y entrevistador; permisos explicados, asignación por nombre de vacante, invitaciones de un uso, estados y cancelación. El entrevistador solo consulta procesos asignados. `/empresa/equipo`. |
| Seguridad reforzada | MFA obligatorio antes de operar, alta mediante QR local y sesiones más breves que las recordadas por candidatos. Acceso y espacio empresarial con composición y navegación propias. |
| Reclutamiento ciego | Protección de identidad en API y pantallas iniciales; revelación explícita y controlada para avanzar al contacto/entrevista. |
| Requisitos ponderados | Habilidades esenciales/deseables y pesos editables que participan en el matching. Dentro de `/empresa/calidad`. |
| Calidad de vacantes | Ocho comprobaciones orientativas con acciones y edición de responsabilidades, requisitos, salario, modalidad, ubicación, plazo y habilidades esenciales/deseables. Referencias salariales internas, sin datos del mercado en tiempo real. `/empresa/calidad`. |
| Contratación por potencial | Bases relacionadas y brechas visibles, sin sustituir una habilidad faltante por una supuesta equivalencia. |
| Gestión y plazos | Etapas, historial, respuesta al candidato, cierre y notificaciones; parámetros de respuesta para procesos nuevos y siguientes avances. |

## Administrador

| Funcionalidad | Implementación y dónde usarla |
| --- | --- |
| Acceso restringido | Sin registro público de administradores. Portal `/acceso-administracion`, MFA y permisos comprobados en backend. |
| SSO corporativo | Google Workspace o Microsoft Entra ID, identidad aprovisionada, MFA y política obligatoria opcional. Sesión vinculada al dominio/tenant y aplicación; sin creación ni elevación automática por correo. |
| Verificación empresarial | Cola de revisión, decisión y motivos, con alcance manual local. `/admin/verificaciones`. |
| Salud y reputación | Plazos incumplidos, comportamiento observable, incidencias revisadas y efecto de reputación en visibilidad. Las denuncias pendientes no penalizan. `/admin/ecosistema`. |
| Auditoría de matching | Versión, componentes y revisión de resultados; métricas sobre datos disponibles. No certifica ausencia de sesgos demográficos. |
| Tendencias internas | Cruce de habilidades/ofertas/candidatos de la base local, sin extrapolar porcentajes al mercado laboral externo. |
| Catálogo educativo | Crear, editar, archivar e importar JSON; validación de enlaces y transparencia de patrocinio/afiliación sin alterar el ranking. `/admin/aprendizaje`. |
| Evaluación de modelos | Método activo, datos disponibles, experimentos de interés, evaluación con usuarios separados y mantenimiento periódico condicionado a datos suficientes. `/admin/modelos`. |
| Trazabilidad | Eventos transaccionales con campos permitidos; sin contraseñas, tokens, consultas SQL ni código fuente. |

## Dependencias que no están activadas en local

- Google, GitHub, LinkedIn, Workspace y Entra ID necesitan aplicaciones y credenciales reales.
  LinkedIn exige HTTPS. Sus pruebas usan proveedores en memoria; no se conectaron
  cuentas reales. Entra requiere un tenant concreto y aprovisionamiento administrativo.
- Catálogos comerciales por API, compras, certificados oficiales y comisiones
  requieren acceso a proveedores y acuerdos. La importación JSON local sí funciona.
- Verificación legal automática de empresas requiere un registro/proveedor oficial.
  La revisión manual local sí funciona.
- Los retos SQL sí ejecutan consultas restringidas. La ejecución arbitraria de
  Python, Java o JavaScript no forma parte de esta versión.
- SMTP incluye cola duradera, reintentos, caducidad y TLS, con pruebas reales contra
  un sumidero local. La entrega externa, VPN, dominios e infraestructura operativa
  siguen pendientes. No se crean recursos facturables con presupuesto cero.
- No existen datos reales suficientes para entrenar predicción de contratación,
  promover un modelo de interés al ranking o auditar equidad demográfica. Las
  cuentas ficticias se excluyen del entrenamiento; no se inventan observaciones.

## Validación de cierre

La validación del 8 de octubre de 2026 comprende dependencias Python, lint de
Python/JavaScript, pruebas backend/frontend, compilación Vite y modelo neuronal
offline. La migración vigente es 0036. Los resultados de la ejecución actual y su
huella de código están en `.local/verification/validation.json` y `rehearsal.json`.

La aceptación entre los tres roles utiliza sesiones reales y MFA, bases
temporales y ningún proveedor externo. PostgreSQL 18 real comprueba migraciones,
concurrencia de la cola de correo y restauración de todas las filas de 27 tablas
en `.local/staging/verification.json`. No conecta a la base original.

La capacidad local utiliza ocho candidatos concurrentes y 50 ofertas sintéticas.
La matriz de regresión comprueba cobertura, identificadores, alias y explicaciones;
SMTP valida certificados y hostname en conexiones SSL/STARTTLS reales, sin entregar
correo externo. Los informes no incluyen credenciales ni datos personales.

La auditoría de dependencias llevó a actualizar Tailwind a 4.3.3 con su plugin
Vite y a retirar la cadena de globbing vulnerable del compilador anterior.
Se conserva el tema del proyecto y se ajustan las utilidades que cambiaron de
nombre. La interfaz requiere navegadores modernos (Chrome 111+, Safari 16.4+,
Firefox 128+), según la [guía oficial de Tailwind](https://tailwindcss.com/docs/upgrade-guide).

La revisión visual usa cuentas QA ficticias independientes y perfiles comerciales,
además de los recorridos técnicos previos. Comprueba el espacio empresarial,
calidad y guardado de ofertas, permisos, recomendaciones con formación,
evidencias y retos por pasos. No modifica las cuentas existentes ni activa
cámara o micrófono.

## Simplificación de navegación

Se retiraron análisis de ZIP/repositorios, salas de entrevista, videollamada,
pizarra y creación de escenarios de trabajo. Los datos históricos permanecen;
las rutas HTTP retiradas responden 404 y las antiguas pantallas redirigen. La
etapa de entrevista del proceso continúa disponible. No se renumeran IDs:
el antiguo `#4` era la clave global de la base; los selectores muestran ahora
el nombre y estado de la vacante.

Mi perfil reúne las evidencias; Recomendaciones reúne compatibilidad,
preferencias, intereses y formación por vacante; Mi desarrollo reúne catálogo,
plan y pasaporte. Empresa reúne requisitos en Calidad de ofertas y verificación,
accesos y asignaciones en Organización y equipo. No muestra controles de
privacidad o aprendizaje propios del candidato.

Los comandos de arranque, configuración, límites y referencias técnicas están en
[DEVELOPMENT.md](DEVELOPMENT.md). Las claves, sesiones, credenciales de ejemplo y
pesos no se incluyen en Git. El servidor local omite logs de acceso para no imprimir
parámetros de callbacks OAuth; conserva los mensajes de errores y arranque.

El flujo completo entre los tres roles pasó con sesiones y MFA en bases temporales.
`scripts/local.py doctor` comprueba la instalación y `scripts/local.py verify`
repite la validación y guarda un informe sin secretos en `.local/verification/`.
La evidencia visual se conserva dentro de esa carpeta. El cierre local y lo
necesario para conectar servicios reales están
en [LOCAL_HANDOFF.md](LOCAL_HANDOFF.md).
