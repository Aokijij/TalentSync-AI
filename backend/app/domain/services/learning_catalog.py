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

LOCAL_RESOURCES = [
    {"id": "project-sql", "title": "Construye un informe de pedidos", "skills": ["sql"], "hours": 3, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Diseña tablas clientes y pedidos. Escribe consultas con filtros, agrupaciones y LEFT JOIN. Incluye clientes sin pedidos y demuestra cómo enlazas parámetros. Guarda el SQL y los casos de prueba en un repositorio y añádelo como evidencia."},
    {"id": "project-python", "title": "Procesa registros con Python y pruebas", "skills": ["python"], "hours": 4, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Procesa una lista de ventas con datos faltantes y calcula totales. Separa lectura, validación y cálculo. Escribe pruebas de entradas vacías, tipos incorrectos y duplicados. Publica el proyecto si quieres y registra la evidencia."},
    {"id": "project-microservices", "title": "Diseña un flujo de pedidos resistente a fallos", "skills": ["microservicios"], "hours": 5, "provider": "TalentSync · proyecto local", "kind": "project", "sponsored": False,
     "instructions": "Diseña los límites de pedidos y pagos. Documenta contratos, idempotencia, timeouts y recuperación ante fallos. Incluye una secuencia de reintentos y explica cuándo preferirías un monolito modular. Añade un diagrama y casos de prueba como evidencia."},
]
