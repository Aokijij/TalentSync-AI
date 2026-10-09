"""Deterministic mini simulations. Answers stay server-side until submission."""
import math


class InvalidActivity(ValueError):
    pass

# A sequence, a calculation and a matching task with concrete sector context.
CASES = {
    "general": ("Coordina una entrega", "Un informe debe entregarse el viernes. Falta validar una cifra y la persona que la conoce estará ausente el jueves.", ["Confirmar alcance y fecha", "Validar la cifra antes del jueves", "Comunicar alternativas si hay retraso", "Entregar y confirmar recepción"], "Se completaron 12 de 20 tareas. ¿Qué porcentaje está completo?", 60, ["Responsable", "Plazo", "Criterio de cierre"], ["Quién ejecuta", "Cuándo se entrega", "Cómo se comprueba el resultado"]),
    "technology": ("Comprueba un registro de solicitudes", "Llegan solicitudes duplicadas y otras sin importe. El sistema debe aceptar cada ID válido una sola vez.", ["Definir entradas y criterios de aceptación", "Validar campos e identificadores", "Procesar registros válidos", "Probar errores y duplicados"], "Llegan 10 registros: 2 tienen campos incompletos y 1 más repite un ID. ¿Cuántos registros únicos válidos quedan?", 7, ["Validación", "Idempotencia", "Autorización"], ["Rechazar datos incompletos", "Evitar efectos duplicados al reintentar", "Comprobar permisos sobre el recurso"]),
    "service": ("Resuelve un cobro duplicado", "Una cliente reclama dos cobros iguales. La devolución requiere revisión de otro equipo y no puedes prometerla antes de verificarla.", ["Escuchar y verificar los cobros", "Registrar el caso y sus soportes", "Escalar con responsable y plazo", "Confirmar la solución con la cliente"], "De 20 solicitudes, se resolvieron 15. ¿Qué porcentaje está resuelto?", 75, ["Escucha", "Escalamiento", "Cierre"], ["Confirmar la necesidad", "Derivar con contexto", "Comprobar la solución"]),
    "sales": ("Prepara una propuesta transparente", "Una tienda compara proveedores para reducir faltantes. Tu producto requiere conexión y el presupuesto es limitado.", ["Explorar necesidad y restricciones", "Comparar alternativas y limitaciones", "Acordar una propuesta viable", "Confirmar siguiente paso y seguimiento"], "Un producto cuesta 200.000 COP. Con un descuento de 10%, ¿cuál es el precio final en COP?", 180000, ["Necesidad", "Limitación", "Seguimiento"], ["Reducir faltantes de inventario", "Requiere conexión", "Revisar el resultado en una fecha acordada"]),
    "administration": ("Recupera el control documental", "Recibes tres versiones de un contrato y un archivo de nómina compartido por error. Solo una versión del contrato está vigente.", ["Restringir la exposición de la nómina", "Identificar la versión vigente", "Registrar responsable y permisos", "Comprobar acceso y trazabilidad"], "Hay 24 expedientes. A 6 les falta firma. ¿Cuántos tienen firma?", 18, ["Versión", "Acceso", "Trazabilidad"], ["Identifica el documento vigente", "Limita quién puede consultar", "Registra quién cambió qué y cuándo"]),
    "finance": ("Concilia dos saldos", "El libro tiene 1.250.000 COP y el banco 1.120.000 COP. Hay un depósito en tránsito de 100.000 COP y una comisión de 30.000 COP no registrada.", ["Confirmar que los saldos tienen el mismo corte", "Identificar depósito y comisión con soportes", "Proponer el registro de la comisión para revisión", "Comprobar que los saldos ajustados coinciden"], "¿Cuál es el saldo conciliado en COP, después de restar la comisión al libro y sumar el depósito al banco?", 1220000, ["Depósito en tránsito", "Comisión", "Soporte"], ["Se suma al saldo bancario para conciliar", "Se resta del libro al registrarla", "Permite revisar el ajuste"]),
    "logistics": ("Recupera el inventario", "El sistema muestra 120 unidades; se cuentan 112, incluidas 5 dañadas. Una salida de 8 aún no se ha registrado.", ["Confirmar conteo y movimientos", "Separar las unidades dañadas", "Registrar la salida con su soporte", "Revisar disponibilidad antes de despachar"], "Se cuentan 112 unidades, incluidas 5 dañadas. ¿Cuántas están disponibles para despachar?", 107, ["Existencia física", "Disponibilidad", "Trazabilidad"], ["Unidades que se cuentan", "Unidades aptas para entregar", "Movimientos con fecha y soporte"]),
    "education": ("Ajusta una actividad accesible", "De 20 participantes, 12 confunden dos conceptos y 3 no pueden acceder al video. Debes ofrecer otra forma de practicar y comprobar el aprendizaje.", ["Identificar la confusión y la barrera de acceso", "Diseñar un ejemplo y una alternativa accesible", "Recoger una nueva evidencia de aprendizaje", "Dar retroalimentación según el criterio"], "12 de 20 participantes requieren refuerzo. ¿Qué porcentaje representa?", 60, ["Objetivo", "Evidencia", "Retroalimentación"], ["Describe lo que podrá hacer", "Muestra lo que realizó", "Explica cómo mejorar con el criterio"]),
    "design": ("Prepara una campaña para una biblioteca", "Una biblioteca requiere una pieza para móvil y un cartel de un taller gratuito. Hay que comprobar legibilidad y permisos de las imágenes.", ["Confirmar público y mensaje", "Proponer jerarquía visual", "Revisar legibilidad y permisos", "Entregar formatos y validar con la audiencia"], "Una campaña tiene 4 piezas y cada una necesita 2 formatos. ¿Cuántos archivos finales hay que entregar?", 8, ["Jerarquía", "Legibilidad", "Permisos"], ["Ordena el mensaje por importancia", "Permite leer en el tamaño de uso", "Autoriza el uso de imágenes"]),
    "care": ("Orienta un trámite de forma confidencial", "En una recepción, alguien solicita datos de un familiar y otra persona necesita orientación administrativa. No puedes divulgar datos clínicos ni dar indicaciones médicas.", ["Verificar identidad, autorización y alcance", "Explicar el trámite con lenguaje claro", "Derivar consultas fuera de tu función", "Registrar solo los datos mínimos"], "De 12 trámites administrativos, 4 requieren derivación. ¿Cuántos puedes atender dentro de tu función?", 8, ["Autorización", "Minimización", "Derivación"], ["Permiso para acceder a información", "Recoger solo datos necesarios", "Enviar al personal competente"]),
}


CALCULATION_GUIDES = {
    "general": "Divide 12 entre 20 y multiplica por 100: 60%.",
    "technology": "Resta los registros incompletos y el duplicado: 10 − 2 − 1 = 7.",
    "service": "Divide las 15 solicitudes resueltas entre 20 y multiplica por 100: 75%.",
    "sales": "El descuento es 200.000 × 0,10 = 20.000 COP. Precio final: 200.000 − 20.000 = 180.000 COP.",
    "administration": "Resta los seis expedientes sin firma: 24 − 6 = 18.",
    "finance": "Libro ajustado: 1.250.000 − 30.000 = 1.220.000 COP. Banco ajustado: 1.120.000 + 100.000 = 1.220.000 COP. Ambos deben coincidir.",
    "logistics": "Las unidades dañadas no están disponibles: 112 − 5 = 107. La salida pendiente explica la diferencia del sistema, no debe descontarse dos veces del conteo físico.",
    "education": "Divide 12 entre 20 y multiplica por 100: 60%. La barrera de acceso necesita además una alternativa accesible.",
    "design": "Multiplica cuatro piezas por dos formatos: 4 × 2 = 8 archivos finales.",
    "care": "Resta los trámites que requieren derivación: 12 − 4 = 8. Atiende únicamente los que corresponden a tu función.",
}


CASES.update({
    "microsoft-data-analytics": ("Prepara un informe de ventas", "Una tabla de 20 ventas contiene 2 filas duplicadas y 3 sin fecha. Antes de visualizarla, necesitas limpiar, relacionar y comprobar sus totales.", ["Definir la pregunta del informe", "Limpiar duplicados y revisar fechas ausentes", "Relacionar tablas y comprobar medidas", "Elegir una visualización y validar totales"], "De 20 filas, 2 son duplicados y otras 3 no tienen fecha válida. ¿Cuántas filas quedan para el informe por fecha?", 15, ["Power Query", "Modelo de datos", "Medida"], ["Transforma y limpia los datos", "Relaciona las tablas del informe", "Calcula un resultado según los filtros"]),
    "project-rest": ("Diseña una API con permisos", "Una API de pedidos permite crear, consultar y cancelar pedidos. Cada cliente solo puede acceder a los suyos y una petición puede reintentarse.", ["Definir recursos y contrato", "Comprobar identidad y autorización por pedido", "Validar datos y procesar sin duplicados", "Probar acceso ajeno y reintentos"], "Se reciben 12 peticiones de creación y 3 repiten una clave de idempotencia ya procesada. ¿Cuántos pedidos nuevos se crean?", 9, ["POST", "GET", "Autorización"], ["Solicita crear un recurso", "Consulta sin modificar el recurso", "Comprueba permiso sobre cada pedido"]),
    "project-git": ("Prepara un cambio revisable", "Hay cambios pendientes en una rama compartida y un conflicto con una corrección de validación. Debes conservar ambos trabajos y entregar un cambio revisable.", ["Revisar estado y proteger cambios pendientes", "Crear un cambio acotado con commits claros", "Resolver el conflicto conservando ambas necesidades", "Ejecutar pruebas y solicitar revisión"], "Una revisión contiene 8 pruebas; 2 fallan. ¿Cuántas pruebas pasan?", 6, ["Commit", "Conflicto", "Revert"], ["Registra un cambio coherente", "Requiere decidir cómo combinar cambios", "Crea un cambio que deshace otro commit"]),
    "project-security": ("Revisa una API de práctica", "Una API consulta documentos por ID y recibe filtros. Debes revisar acceso indebido, inyección y exposición de datos sin usar información real.", ["Identificar datos y límites de confianza", "Diseñar pruebas autorizadas de riesgos", "Aplicar autorización y consultas parametrizadas", "Repetir pruebas y documentar limitaciones"], "Se revisan 15 casos de acceso; 4 permiten consultar un documento ajeno. ¿Cuántos casos respetan el control de acceso?", 11, ["Autorización", "Parámetros", "Minimización"], ["Restringe acceso al documento", "Separa datos de instrucciones SQL", "Evita exponer datos innecesarios"]),
    "project-sql": ("Construye un informe de pedidos", "Tres clientes tienen respectivamente 2, 0 y 3 pedidos pagados. El informe debe incluir también a los clientes sin pedidos y evitar duplicar totales.", ["Definir tablas y relación de pedidos", "Conservar clientes sin pedidos con LEFT JOIN", "Agrupar por cliente y tratar los NULL", "Comparar totales con datos de prueba"], "Los clientes tienen 2, 0 y 3 pedidos pagados. ¿Cuántos pedidos pagados debe sumar el informe?", 5, ["LEFT JOIN", "GROUP BY", "COALESCE"], ["Conserva filas de la tabla izquierda", "Agrupa registros por una clave", "Sustituye un valor NULL"]),
    "project-python": CASES["technology"],
    "project-microservices": ("Recupera un flujo de pedidos", "Pedidos y pagos se comunican con un proveedor que puede tardar. Una petición puede repetirse y debe conservar la misma clave de idempotencia.", ["Definir responsabilidades y contrato", "Asignar clave de idempotencia y timeout", "Reintentar fallos transitorios con límite", "Seguir la petición y comprobar recuperación"], "Se envían 4 intentos de cobro con la misma clave de idempotencia válida. ¿Cuántos cobros debe producir el proveedor?", 1, ["Timeout", "Idempotencia", "Trazabilidad"], ["Limita el tiempo de espera", "Evita duplicar el efecto al reintentar", "Permite seguir una petición entre servicios"]),
})

CALCULATION_GUIDES.update({
    "microsoft-data-analytics": "Primero identifica las filas que requieren revisión: 20 − 2 − 3 = 15. Conserva los registros excluidos para corregir su origen, sin inventar fechas.",
    "project-rest": "Las peticiones repetidas no crean pedidos adicionales: 12 − 3 = 9.",
    "project-git": "Pruebas que pasan: 8 − 2 = 6. Las dos que fallan requieren revisión antes de compartir.",
    "project-security": "Casos que respetan el acceso: 15 − 4 = 11. Los cuatro accesos indebidos siguen siendo fallos que deben corregirse.",
    "project-sql": "Suma los pedidos pagados de cada cliente: 2 + 0 + 3 = 5. El cliente sin pedidos debe conservarse con total cero.",
    "project-python": CALCULATION_GUIDES["technology"],
    "project-microservices": "La misma clave identifica una única operación: cuatro intentos deben producir un solo cobro.",
})


def activity_key(resource):
    return resource["id"] if resource.get("id") in CASES else resource.get("category", "general")


def activities_for(area):
    _, _, sequence, prompt, answer, terms, meanings = CASES.get(area, CASES["general"])
    # The presentation order is deliberately different from the solution.
    return [
        {"id": "sequence", "type": "order", "prompt": "Organiza el flujo de trabajo del caso, de principio a fin.", "choices": [sequence[2], sequence[0], sequence[3], sequence[1]], "answer": [1, 3, 0, 2], "feedback": " → ".join(sequence)},
        {"id": "calculation", "type": "number", "prompt": prompt, "choices": [], "answer": answer, "feedback": CALCULATION_GUIDES.get(area, CALCULATION_GUIDES["general"])},
        {"id": "connections", "type": "matching", "prompt": "Relaciona cada concepto con su función.", "terms": terms, "choices": [meanings[1], meanings[2], meanings[0]], "answer": [2, 0, 1], "feedback": "; ".join(f"{term}: {meaning}" for term, meaning in zip(terms, meanings, strict=True))},
    ]


def public_activity(item):
    return {key: value for key, value in item.items() if key not in {"answer", "feedback"}}


def evaluate(item, value):
    kind = item.get("type", "choice")
    if kind == "number":
        if type(value) not in {int, float, str}:
            raise InvalidActivity("Introduce una cantidad numérica")
        try:
            number = float(value)
        except (ValueError, OverflowError):
            raise InvalidActivity("Introduce una cantidad numérica válida") from None
        if not math.isfinite(number):
            raise InvalidActivity("La cantidad debe ser finita")
        return abs(number - item["answer"]) < 0.001
    if kind in {"order", "matching", "multi_select"}:
        if not isinstance(value, list) or any(type(index) is not int or not 0 <= index < len(item["choices"]) for index in value) or len(set(value)) != len(value):
            raise InvalidActivity("Selecciona valores válidos sin repetir")
        if kind in {"order", "matching"} and len(value) != len(item["answer"]):
            raise InvalidActivity("Completa todos los elementos de la actividad")
        return sorted(value) == sorted(item["answer"]) if kind == "multi_select" else value == item["answer"]
    if type(value) is not int or not 0 <= value < len(item["choices"]):
        raise InvalidActivity("Selecciona una opción válida para cada pregunta")
    return value == item["answer"]


def mixed_banks(exercises):
    banks = {}
    technology = ("Validación y pruebas de datos", "python", CASES["technology"][1], [("Un registro no incluye identificador. ¿Cómo lo procesas?", ["Aceptarlo como si fuera válido", "Rechazarlo con un error comprensible", "Inventar un identificador sin registrar el cambio"], 1, "Los campos necesarios se validan antes de procesar el registro.")])
    for area, (title, skill, context, questions) in {**exercises, "technology": technology}.items():
        prompt, choices, answer, feedback = questions[0]
        activities = activities_for(area)
        banks[f"{area}-simulation-v1"] = {"title": f"Laboratorio: {title.lower()}", "skill": skill, "category": area, "context": CASES[area][1], "version": "1", "minutes": 15,
            "questions": [{"id": "decision", "prompt": prompt, "choices": choices, "answer": answer, "feedback": feedback}, *activities,
                          {"id": "review", "type": "multi_select", "prompt": "Selecciona las dos acciones que permiten revisar tu trabajo.", "choices": ["Conservar soportes sin exponer datos personales", "Ocultar las limitaciones", "Comparar el resultado con un criterio acordado", "Dar por correcto el resultado sin comprobarlo"], "answer": [0, 2], "feedback": "Conserva los soportes necesarios y comprueba el resultado con un criterio explícito."}]}
    return banks
