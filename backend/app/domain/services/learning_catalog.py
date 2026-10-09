"""Original local exercises. They are not external courses or certifications."""

ASSESSMENTS = {
    "sql-foundations-v1": {"title": "Fundamentos de consultas SQL", "skill": "sql", "version": "1", "minutes": 10,
        "questions": [
            {"id": "filter", "prompt": "Necesitas solo pedidos con total mayor a 100. ¿Qué cláusula filtra las filas antes de agrupar?", "choices": ["WHERE total > 100", "HAVING total > 100", "ORDER BY total"], "answer": 0, "feedback": "WHERE filtra filas; HAVING filtra grupos."},
            {"id": "join", "prompt": "Debes listar todos los clientes, incluso los que no tienen pedidos. ¿Qué unión corresponde?", "choices": ["INNER JOIN pedidos", "LEFT JOIN pedidos desde clientes", "CROSS JOIN pedidos"], "answer": 1, "feedback": "LEFT JOIN preserva los registros de la tabla izquierda."},
            {"id": "null", "prompt": "¿Cómo seleccionas registros cuyo correo es NULL?", "choices": ["correo = NULL", "correo = ''", "correo IS NULL"], "answer": 2, "feedback": "NULL se comprueba con IS NULL."},
            {"id": "count", "prompt": "Tras un LEFT JOIN, ¿cómo cuentas únicamente los pedidos existentes de cada cliente?", "choices": ["COUNT(*)", "COUNT(pedidos.id)", "SUM(clientes.id)"], "answer": 1, "feedback": "COUNT(columna) omite valores NULL."},
            {"id": "parameter", "prompt": "Un buscador recibe texto del usuario. ¿Qué evita inyección SQL?", "choices": ["Concatenar texto con comillas", "Quitar espacios al texto", "Usar parámetros enlazados"], "answer": 2, "feedback": "Los parámetros separan los datos del código SQL."},
        ]},
    "python-foundations-v1": {"title": "Fundamentos de Python", "skill": "python", "version": "1", "minutes": 10,
        "questions": [
            {"id": "alias", "prompt": "a = [1]; b = a; b.append(2). ¿Cuánto vale a?", "choices": ["[1]", "[1, 2]", "[2]"], "answer": 1, "feedback": "Ambas variables apuntan a la misma lista."},
            {"id": "dict", "prompt": "Necesitas un valor predeterminado si una clave no existe en un dict. ¿Qué usas?", "choices": ["datos.get('clave', 0)", "datos['clave'] or 0", "datos.append(0)"], "answer": 0, "feedback": "dict.get acepta un valor predeterminado sin lanzar KeyError."},
            {"id": "exception", "prompt": "Una operación puede lanzar ValueError. ¿Cómo evitas ocultar otros errores?", "choices": ["except: pass", "except BaseException: pass", "except ValueError: manejar el caso"], "answer": 2, "feedback": "Captura la excepción específica que sabes manejar."},
            {"id": "mutable", "prompt": "¿Qué firma evita compartir una lista mutable entre llamadas?", "choices": ["def f(items=[])", "def f(items=None) y crear la lista dentro", "def f(items=list())"], "answer": 1, "feedback": "Los argumentos predeterminados se evalúan una vez al definir la función."},
            {"id": "test", "prompt": "¿Qué prueba cubre mejor una función que divide dos números?", "choices": ["Solo 10 / 2", "Casos normales, negativos y división por cero", "Solo comprobar el nombre de la función"], "answer": 1, "feedback": "Combina casos representativos y límites."},
        ]},
    "microservices-foundations-v1": {"title": "Decisiones básicas de microservicios", "skill": "microservicios", "version": "1", "minutes": 10,
        "questions": [
            {"id": "boundary", "prompt": "Pedidos y facturación cambian a ritmos distintos. ¿Qué criterio ayuda a separar servicios?", "choices": ["Una tabla por servicio siempre", "Responsabilidades y límites del negocio", "Una función por servicio"], "answer": 1, "feedback": "Los límites del negocio ayudan a mantener responsabilidades coherentes."},
            {"id": "retry", "prompt": "Un pago se reintenta después de un timeout. ¿Qué evita cobrar dos veces?", "choices": ["Reintentar sin límite", "Quitar los logs", "Una clave de idempotencia persistente"], "answer": 2, "feedback": "La idempotencia reconoce una operación repetida."},
            {"id": "timeout", "prompt": "El servicio externo falla durante minutos. ¿Qué protege tu aplicación?", "choices": ["Timeouts, límites de reintento y circuit breaker", "Esperar indefinidamente", "Crear más hilos sin límite"], "answer": 0, "feedback": "Limitar esperas y reintentos reduce fallos en cascada."},
            {"id": "trace", "prompt": "Una petición atraviesa cuatro servicios. ¿Qué facilita seguirla?", "choices": ["Borrar logs exitosos", "Un identificador de traza propagado", "Cambiar de ID en cada servicio sin vínculo"], "answer": 1, "feedback": "Las trazas correlacionan los pasos de una misma petición."},
            {"id": "tradeoff", "prompt": "Un equipo pequeño inicia un producto sin límites de dominio claros. ¿Qué decisión es razonable?", "choices": ["Crear decenas de servicios de inmediato", "Usar microservicios para toda función", "Empezar modular y separar cuando exista una necesidad medible"], "answer": 2, "feedback": "La distribución añade costes operativos; debe responder a una necesidad."},
        ]},
}

ASSESSMENTS.update({
    "rest-foundations-v1": {"title": "Fundamentos de APIs REST", "skill": "api rest", "version": "1", "minutes": 10,
        "questions": [
            {"id": "read", "prompt": "¿Qué método corresponde a consultar un recurso sin modificarlo?", "choices": ["GET", "DELETE", "POST"], "answer": 0, "feedback": "GET consulta; las operaciones de lectura no deben introducir cambios de negocio."},
            {"id": "access", "prompt": "Un usuario autenticado intenta leer el documento privado de otra persona. ¿Dónde compruebas la autorización?", "choices": ["Solo ocultando el botón", "En el backend para ese recurso y usuario", "Confiando en el ID recibido"], "answer": 1, "feedback": "La autorización por recurso se comprueba en el servidor, aunque la interfaz o el ID se manipulen."},
            {"id": "retry", "prompt": "Un cliente reintenta crear un pedido tras perder la respuesta. ¿Qué evita crear otro pedido?", "choices": ["Reintentar indefinidamente", "Cambiar el ID en cada reintento", "Una clave de idempotencia asociada al resultado"], "answer": 2, "feedback": "Una clave de idempotencia permite reconocer el mismo intento y recuperar su resultado."},
            {"id": "conflict", "prompt": "Dos personas editan la misma versión de una vacante. ¿Cómo evitas sobrescribir silenciosamente el primer cambio?", "choices": ["Validar la versión y devolver un conflicto al segundo cambio", "Aceptar siempre el último cambio", "Ocultar la fecha de modificación"], "answer": 0, "feedback": "El control de versión permite detectar un cambio concurrente y solicitar actualización."},
            {"id": "validation", "prompt": "La API recibe un salario negativo aunque el formulario lo impide. ¿Qué corresponde?", "choices": ["Guardarlo porque lo envió el frontend", "Validar y rechazarlo también en el backend", "Corregirlo a cero sin avisar"], "answer": 1, "feedback": "Las reglas del negocio se validan en el servidor; el formulario no es una barrera de confianza."},
        ]},
    "git-foundations-v1": {"title": "Control de versiones con Git", "skill": "git", "version": "1", "minutes": 10,
        "questions": [
            {"id": "status", "prompt": "Antes de preparar un commit, ¿cómo revisas los archivos modificados y preparados?", "choices": ["git status y git diff", "git push --force", "git init en cada carpeta"], "answer": 0, "feedback": "Revisar estado y diferencias permite seleccionar y comprobar lo que vas a versionar."},
            {"id": "secret", "prompt": "Una clave privada entró en un commit ya compartido. ¿Cuál es la primera medida sobre la credencial?", "choices": ["Solo borrar el archivo del siguiente commit", "Rotarla o revocarla y tratar la exposición", "Renombrar el archivo"], "answer": 1, "feedback": "Borrar un archivo no elimina una credencial del historial ni de copias anteriores."},
            {"id": "conflict", "prompt": "Una fusión deja marcadores de conflicto. ¿Cómo la completas?", "choices": ["Publicar los marcadores", "Borrar todos los cambios de la otra persona", "Revisar ambas versiones, resolver, comprobar y preparar el resultado"], "answer": 2, "feedback": "Resolver un conflicto exige conservar el comportamiento correcto y comprobar el resultado."},
            {"id": "revert", "prompt": "Quieres deshacer un commit de una rama compartida conservando el historial. ¿Qué operación suele corresponder?", "choices": ["git revert del commit", "Borrar la carpeta .git", "Reescribir siempre la rama con force"], "answer": 0, "feedback": "Revert crea un nuevo commit que invierte el cambio sin borrar la historia compartida."},
            {"id": "review", "prompt": "¿Qué facilita revisar y recuperar una funcionalidad?", "choices": ["Mezclar todos los cambios pendientes", "Commits coherentes con un propósito y validación claros", "Guardar secretos para reproducir el entorno"], "answer": 1, "feedback": "Un cambio coherente y validado facilita revisión, comparación y recuperación."},
        ]},
    "application-security-foundations-v1": {"title": "Seguridad básica de aplicaciones", "skill": "seguridad de aplicaciones", "version": "1", "minutes": 10,
        "questions": [
            {"id": "password", "prompt": "¿Cómo almacenas contraseñas para verificarlas después?", "choices": ["Texto plano", "Un hash específico para contraseñas con sal", "Base64"], "answer": 1, "feedback": "Las contraseñas se verifican con funciones de hash diseñadas para ese propósito; no se recuperan en texto plano."},
            {"id": "csrf", "prompt": "Una API usa cookies de sesión. ¿Qué ayuda a proteger una petición que modifica datos frente a CSRF?", "choices": ["Solo CORS", "Poner el token en la URL", "Validar un token CSRF ligado a la sesión y el origen cuando corresponda"], "answer": 2, "feedback": "CORS por sí solo no evita toda petición cruzada; las mutaciones deben validar las protecciones de sesión."},
            {"id": "sql", "prompt": "¿Cómo incorporas datos del usuario a una consulta SQL?", "choices": ["Con parámetros enlazados", "Concatenando comillas", "Sustituyendo espacios"], "answer": 0, "feedback": "Los parámetros separan los datos del código SQL."},
            {"id": "log", "prompt": "Un proveedor devuelve un error que contiene un token. ¿Qué registras?", "choices": ["El error completo y todos los headers", "Una categoría y contexto no sensible suficiente para diagnosticar", "La contraseña para reproducirlo"], "answer": 1, "feedback": "Los registros deben ayudar a diagnosticar sin revelar credenciales, tokens ni datos personales."},
            {"id": "upload", "prompt": "Un archivo subido afirma ser un PDF. ¿Qué comprobaciones corresponden?", "choices": ["Confiar solo en la extensión", "Abrirlo como un programa", "Límites de tamaño, tipo/contenido y tratamiento restringido"], "answer": 2, "feedback": "El nombre del archivo no garantiza su contenido ni que pueda procesarse sin límites."},
        ]},
})

LOCAL_RESOURCES = [
    {"id": "project-sql", "title": "Construye un informe de pedidos", "skills": ["sql"], "hours": 3, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Diseña tablas clientes y pedidos. Escribe consultas con filtros, agrupaciones y LEFT JOIN. Incluye clientes sin pedidos y demuestra cómo enlazas parámetros. Guarda el SQL y los casos de prueba en un repositorio y añádelo como evidencia."},
    {"id": "project-python", "title": "Procesa registros con Python y pruebas", "skills": ["python"], "hours": 4, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Procesa una lista de ventas con datos faltantes y calcula totales. Separa lectura, validación y cálculo. Escribe pruebas de entradas vacías, tipos incorrectos y duplicados. Publica el proyecto si quieres y registra la evidencia."},
    {"id": "project-microservices", "title": "Diseña un flujo de pedidos resistente a fallos", "skills": ["microservicios"], "hours": 5, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Diseña los límites de pedidos y pagos. Documenta contratos, idempotencia, timeouts y recuperación ante fallos. Incluye una secuencia de reintentos y explica cuándo preferirías un monolito modular. Añade un diagrama y casos de prueba como evidencia."},
    {"id": "project-rest", "title": "Diseña una API de pedidos con permisos", "skills": ["api rest"], "hours": 4, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Documenta consulta, creación y edición de pedidos. Define validación, permisos por recurso, errores, idempotencia y conflictos de versión. Añade ejemplos de peticiones y casos negativos sin incluir credenciales reales."},
    {"id": "project-git", "title": "Entrega un cambio revisable con Git", "skills": ["git"], "hours": 2, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "En un repositorio de práctica, crea una rama, divide un cambio en commits coherentes, resuelve un conflicto y revierte un commit conservando el historial. Documenta las comprobaciones y excluye secretos del repositorio."},
    {"id": "project-security", "title": "Revisa la seguridad de una API de práctica", "skills": ["seguridad de aplicaciones"], "hours": 4, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Usa una aplicación ficticia propia. Documenta validación, autorización por recurso, sesiones/CSRF, tratamiento de archivos y protección de logs. Escribe casos negativos con datos sintéticos y explica las correcciones; no pruebes sistemas ajenos."},
]


from app.domain.services.career_learning import assessment_banks, practice_resources

for bank in ASSESSMENTS.values():
    bank["category"] = "technology"
for resource in LOCAL_RESOURCES:
    resource["category"] = "technology"
ASSESSMENTS.update(assessment_banks())
LOCAL_RESOURCES.extend(practice_resources())

# Direct provider pages reviewed on 2026-10-08; no affiliate or remote catalog calls.
LOCAL_RESOURCES.extend([
    {"id": "hubspot-inbound-sales", "category": "sales", "title": "Ventas inbound · curso con certificación del proveedor", "skills": ["ventas"], "hours": 3.1,
     "provider": "HubSpot Academy", "kind": "course", "sponsored": False, "url": "https://academy.hubspot.com/courses/inbound-sales",
     "instructions": "Curso gratuito de venta consultiva y conversaciones comerciales, con opción en español. Requiere cuenta externa y evaluación del proveedor. La certificación no se emite ni verifica automáticamente en TalentSync."},
    {"id": "microsoft-data-analytics", "category": "technology", "title": "Introducción al análisis de datos de Microsoft", "skills": ["power bi"], "hours": 3,
     "provider": "Microsoft Learn", "kind": "course", "sponsored": False, "url": "https://learn.microsoft.com/es-es/training/paths/data-analytics-microsoft/",
     "instructions": "Ruta de cuatro módulos sobre análisis de datos y Power BI. Tiempo de estudio orientativo. La formación es independiente de los exámenes de certificación y puede requerir herramientas del proveedor para la práctica."},
])

from app.domain.services.career_learning import EXERCISES
from app.domain.services.learning_activities import mixed_banks

ASSESSMENTS.update(mixed_banks(EXERCISES))
