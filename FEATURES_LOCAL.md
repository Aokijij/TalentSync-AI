# Funcionalidades de la versión local

Proyecto compatible con su stack existente: FastAPI, React y SQLAlchemy.
Rama `codex/desarrollo-funcionalidades-local`, bloques 1–24.
No se realizó despliegue ni push. Los datos de demostración son ficticios y la
base aislada vive en `.local/talentsync.sqlite3`.

## Candidato

| Funcionalidad | Implementación y dónde usarla |
| --- | --- |
| Registro y bienvenida | Correo/contraseña, verificación mediante bandeja local y bienvenida para completar perfil y preferencias. |
| Acceso social | Adaptadores Google, GitHub y LinkedIn; vinculación y retirada con reautenticación, MFA cuando corresponde y control de sesión. Desactivados sin configuración real. |
| Acceso persistente y recuperable | Sesiones opacas revocables, recordar dispositivo personal, recuperar acceso, cambiar correo y segundo factor opcional. `/seguridad`. |
| Compatibilidad bidireccional | Habilidades, contexto semántico, formación, certificados, idiomas y preferencias de salario, modalidad y ubicación. `/compatibilidad` y recomendaciones. |
| Explicaciones de compatibilidad | Componentes ponderados, requisitos esenciales, datos ausentes, brechas y bases relacionadas. La relación entre habilidades no acredita dominio. |
| Semántica multilingüe | Modelo MiniLM activo en CPU, con pesos locales verificados y sin inferencia remota. El porcentaje es un índice de afinidad. |
| Seguimiento de procesos | Etapas, historial, plazos, notificaciones y cierre automático por falta de respuesta; feedback basado en datos registrados, separado de la razón real del reclutador. `/procesos/{id}`. |
| Aprendizaje dirigido | Brecha por vacante, recursos asociados, estimación hipotética de mejora por hora y otras vacantes examinadas, excluyendo la seleccionada. `/aprendizaje`. |
| Plan de práctica | Guardar recursos, marcar progreso y conservar planes aunque se archive un recurso. Completar el plan no acredita la habilidad. |
| Brechas recurrentes | Patrones de habilidades pendientes en procesos finalizados, sin atribuir automáticamente el rechazo a esa brecha. |
| Micropruebas | Evaluaciones locales de fundamentos SQL, Python y microservicios; tiempo limitado, entrega única, repetición limitada y feedback. |
| Retos SQL reales | Dos retos originales, vista previa y entrega contra tres conjuntos sintéticos, en SQLite aislada y restringida. |
| Pasaporte de habilidades | Resultados, versión, alcance y caducidad. Aprobaciones de fundamentos integradas con el perfil. |
| Portafolio y análisis de proyectos | Evidencias manuales, análisis estático de ZIP local y adaptador optativo para repositorios públicos GitHub. Vista previa antes de guardar; sin ejecución ni verificación de autoría. |
| Personalización consentida | Intereses, ofertas ocultas, recuperación de decisiones y señal colaborativa agregada con mínimo de vecinos. `/mis-intereses`. |
| Privacidad | Consentimientos independientes para personalización, evidencia y avisos de nuevas habilidades; retirada de señales y artefactos aprendidos asociados. `/seguridad`. |

## Empresa

| Funcionalidad | Implementación y dónde usarla |
| --- | --- |
| Registro empresarial y revisión | Verificación de correo, organización pendiente y revisión administrativa local. Publicación condicionada a aprobación. |
| Equipo y permisos | Propietario, reclutador y entrevistador; invitaciones de un uso, asignación de vacantes y revocación. `/empresa/equipo`. |
| Seguridad reforzada | MFA obligatorio antes de operar y sesiones más breves que las recordadas por candidatos. |
| Reclutamiento ciego | Protección de identidad en API y pantallas iniciales; revelación explícita y controlada para avanzar al contacto/entrevista. |
| Requisitos ponderados | Habilidades esenciales/deseables y pesos editables que participan en el matching. `/compatibilidad`. |
| Calidad de vacantes | Avisos sobre requisitos, transparencia salarial y referencias internas disponibles; no se presentan como datos salariales del mercado en tiempo real. `/empresa/calidad`. |
| Contratación por potencial | Bases relacionadas y brechas visibles, sin sustituir una habilidad faltante por una supuesta equivalencia. |
| Escenarios laborales | Configuración y revisión de decisiones sobre situaciones del equipo; sin diagnóstico psicométrico ni puntuación de personalidad. |
| Gestión y plazos | Etapas, historial, respuesta al candidato, cierre y notificaciones; parámetros de respuesta para procesos nuevos y siguientes avances. |
| Entrevistas integradas | Sala por proceso, editor compartido, pizarra, control de versiones y presencia. Acceso ligado al proceso y asignación actual. `/entrevistas`. |
| Videollamada | WebRTC de dos participantes, activación explícita de cámara/micrófono y señalización autenticada efímera; adaptador STUN/TURN con credenciales temporales. |

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
- La lectura pública de GitHub está desactivada por defecto y exige consentimiento
  por consulta. No se analizaron repositorios reales.
- Catálogos comerciales por API, compras, certificados oficiales y comisiones
  requieren acceso a proveedores y acuerdos. La importación JSON local sí funciona.
- Verificación legal automática de empresas requiere un registro/proveedor oficial.
  La revisión manual local sí funciona.
- STUN/TURN está integrado en el código, pero no hay un servidor de retransmisión
  instalado/configurado ni prueba audiovisual entre redes externas.
- Los retos SQL sí ejecutan consultas restringidas. La ejecución arbitraria de
  Python, Java o JavaScript requiere un ejecutor aislado adicional; el editor de
  entrevistas no ejecuta código.
- VPN, dominios separados, correo real, infraestructura y despliegue quedan fuera
  de esta entrega local.
- No existen datos reales suficientes para entrenar predicción de contratación,
  promover un modelo de interés al ranking o auditar equidad demográfica. Las
  cuentas ficticias se excluyen del entrenamiento; no se inventan observaciones.

## Validación de cierre

El 8 de octubre de 2026 pasaron 304 pruebas backend y 20 frontend, lint completo
de Python/JavaScript, compilación Vite y comprobación de dependencias Python.
Entra ID añade validación de firma, tenant, audiencia,
caducidad, MFA y revocación; la migración 0035 conserva datos y sesiones previos.
La suite usó bases temporales aisladas, y las migraciones comprobaron SQLite y
generación SQL PostgreSQL sin conexión a la base anterior.

La inferencia real offline pasó con textos sintéticos. Por HTTP local, tres
recomendaciones devolvieron el método neuronal activo en 0,97 s; se comprobaron
aprendizaje, pasaporte, entrevistas, identidades sociales, permisos y logout.
En navegador, una cuenta ficticia independiente completó un reto SQL, superó las
tres comprobaciones y recibió la acreditación de fundamentos en su pasaporte.
La captura está en `.local/verification/retos-sql.jpg`, fuera de Git.

Los comandos de arranque, configuración, límites y referencias técnicas están en
[DEVELOPMENT.md](DEVELOPMENT.md). Las claves, sesiones, credenciales de ejemplo y
pesos no se incluyen en Git. El servidor local omite logs de acceso para no imprimir
parámetros de callbacks OAuth; conserva los mensajes de errores y arranque.

El flujo completo entre los tres roles pasó con sesiones y MFA en bases temporales.
`scripts/local.py doctor` comprueba la instalación y `scripts/local.py verify`
repite la validación y guarda un informe sin secretos en `.local/verification/`.
La evidencia visual más reciente está en `cierre-local-aprendizaje.png` dentro de
esa carpeta. El cierre local y lo necesario para conectar servicios reales están
en [LOCAL_HANDOFF.md](LOCAL_HANDOFF.md).
