"""Review scenarios, all fictional and excluded from model training."""

# key, name, profession, skills, purpose
CANDIDATES = [
    ("nuevo", "Ana Inicio", None, [], "Perfil vacío: bienvenida, edición del perfil, carga de CV y primeras postulaciones."),
    ("sin_correo", "Luis Confirmación", None, [], "Correo sin confirmar: confirmación, recuperación de contraseña y bandeja local."),
    ("senior", "Elena Vargas", "Desarrolladora backend Python", ["python", "sql", "fastapi", "git", "api rest", "pruebas de software", "comunicacion", "organizacion"], "Perfil completo, buenas coincidencias, evidencias, idiomas, guardadas, ocultas y empresa seguida."),
    ("junior", "Tomás Mejía", "Desarrollador junior", ["python", "git"], "Poca experiencia, brechas, formación sugerida y selección anónima inicial."),
    ("transicion", "Natalia Cambio", "Asistente administrativa", ["excel", "organizacion", "gestion documental", "comunicacion"], "Cambio de área hacia datos: bases relacionadas, requisitos pendientes y recomendaciones distintas."),
    ("aprendizaje", "Sofía Avance", "Analista de datos", ["sql", "excel", "python"], "Práctica sin empezar, borrador, publicación; retos aprobado, no aprobado, caducado y SQL práctico."),
    ("plan_lleno", "Pedro Constancia", "Desarrollador de software", ["python", "sql", "git"], "Tres recursos activos: límite del plan, abandono y reanudación de un recurso archivado."),
    ("privacidad", "Lucía Reserva", "Desarrolladora backend", ["python", "sql", "fastapi"], "Consentimientos desactivados: evidencia privada, personalización desactivada y estado vacío de avisos."),
    ("historial", "Andrés Recorrido", "Analista de desarrollo", ["python", "git", "excel"], "Todas las etapas, entrevista, contratación, rechazo, retirada, cierre por plazo e incidencias en cinco estados."),
    ("condiciones", "Daniela Preferencias", "Ingeniera de datos", ["python", "sql", "excel", "git"], "Salario, ciudad y modalidad imprescindibles: ofertas compatibles, conflictivas y con datos ausentes."),
    ("logistica", "Diego Bodega", "Analista de inventarios", ["inventarios", "excel", "organizacion", "logistica"], "Área no tecnológica, trayectoria logística y proceso personalizado."),
    ("creativo", "Paula Diseño", "Diseñadora de interfaces", ["figma", "prototipado", "diseno ux", "accesibilidad"], "Área creativa, portafolio declarado y aprendizaje de diseño."),
]

# key, name, verification state, purpose
COMPANIES = [
    ("empresa", "Horizonte Producto", "verified", "Propietario: ofertas, calidad, selección anónima/visible, etapas estándar/personalizadas, equipo y confianza favorable."),
    ("riesgo", "Delta Seguimiento", "verified", "Plazos vencidos, confianza reducida, incidencias confirmadas y apelación disponible/pendiente."),
    ("vacia", "Semilla Equipo", "verified", "Empresa aprobada sin vacantes ni candidatos: crear la primera oferta y comprobar estados vacíos."),
    ("pendiente", "Inicio Organización", "pending", "Correo no confirmado y solicitud sin presentar; confirmar y solicitar revisión."),
    ("revision", "Norte Servicios", "reviewing", "Solicitud presentada: administrador puede aprobar, pedir información o rechazar."),
    ("correcciones", "Prisma Documental", "information_required", "Correcciones solicitadas: modificar soportes y volver a presentar."),
    ("rechazada", "Ruta Solicitud", "rejected", "Solicitud rechazada con motivo: corregir y volver a solicitar."),
    ("suspendida", "Pausa Operaciones", "suspended", "Suspensión administrativa, oferta pausada y acceso restringido con motivo visible."),
]

TEAM = [
    ("reclutador", "Carolina Selección", "recruiter", True, "Gestiona vacantes y procesos de Horizonte; no administra propietarios ni permisos."),
    ("entrevistador", "Jorge Entrevista", "interviewer", True, "Solo consulta seguimiento de la vacante Backend asignada, desde Organización y equipo."),
    ("revocado", "Mario Acceso retirado", "recruiter", False, "Acceso retirado: comprueba la restricción; el propietario puede reactivarlo."),
    ("invitado", "Andrea Invitación", "recruiter", None, "Invitación pendiente lista para aceptar desde la bandeja local o el enlace de esta guía."),
    ("invitacion_vencida", "Felipe Invitación vencida", "interviewer", None, "Enlace vencido: comprueba rechazo y crea una invitación nueva desde el propietario."),
]

# key, title, skills, salary, modality, lifecycle, blind
JOBS = [
    ("backend", "Backend Python · proceso completo", ["python", "sql", "fastapi", "git", "api rest"], 6500000, "remote", "active", True),
    ("datos", "Analista de datos · perfil visible", ["sql", "python", "excel", "power bi"], 4800000, "hybrid", "active", False),
    ("frontend", "Frontend React · varias habilidades", ["react", "javascript", "html", "css", "git", "accesibilidad", "pruebas de software", "api rest"], 5500000, "remote", "active", True),
    ("qa", "QA de automatización", ["python", "pruebas de software", "git"], 4600000, "hybrid", "active", False),
    ("api", "Desarrollador de APIs", ["python", "sql", "api rest"], 5800000, "remote", "active", True),
    ("soporte", "Analista de soporte", ["servicio al cliente", "comunicacion", "sql"], 3000000, "onsite", "active", False),
    ("lider", "Líder de ingeniería", ["python", "arquitectura de software", "liderazgo", "git"], 8500000, "hybrid", "active", True),
    ("inventarios", "Analista de inventarios · etapas propias", ["inventarios", "excel", "organizacion"], 3200000, "onsite", "active", True),
    ("diseno", "Diseñador de interfaces", ["figma", "prototipado", "accesibilidad"], 4200000, "remote", "active", False),
    ("sin_datos", "Desarrollador Python · condiciones por acordar", ["python", "git"], None, "remote", "active", False),
    ("borrador", "Ingeniero de plataforma · borrador", ["python", "git"], 6000000, "remote", "draft", True),
    ("pausada", "Analista de servicio · pausada", ["comunicacion", "excel"], 2800000, "onsite", "paused", True),
    ("cubierta", "Analista de datos · cubierta", ["sql", "python"], 4500000, "hybrid", "filled", False),
    ("cerrada", "Analista de datos · cierre sin contratación", ["sql", "excel"], 4000000, "hybrid", "closed", False),
    ("baja_calidad", "Asistente · completar condiciones", ["organizacion"], None, "onsite", "draft", False),
]

BOUNDARIES = [
    "Las cuentas, empresas, procesos, evidencias y resultados precargados son simulaciones. No representan contratación, certificación ni denuncias reales.",
    "Google/GitHub/LinkedIn, SSO corporativo, correo externo, importación por API y verificación oficial requieren credenciales/proveedores reales. Puedes revisar su estado y probar los recorridos locales disponibles; no se simula que estén conectados.",
    "Los datos de example.com se excluyen del entrenamiento. Motor e integraciones seguirá mostrando muestra real insuficiente; puedes ejecutar su evaluación y auditoría, sin fabricar un modelo listo ni alterar el ranking.",
    "MFA administrativo se configura en Seguridad en el primer ingreso. No se desactiva ni se reemplaza la protección de cuentas anteriores. MFA empresarial depende de la configuración local.",
    "Los plazos y enlaces son relativos a la fecha de creación. Las invitaciones pendientes vencen a los tres días; los retos cronometrados se inician al probarlos. Repetir la carga conserva los cambios realizados, no reinicia escenarios.",
]
