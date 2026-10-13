"""Resource-aware local practice, with private solutions and stable attempts.

These are editorial transfer exercises, never provider exams or certificates.
"""
import math
import re
import unicodedata
from copy import deepcopy

from app.domain.services.learning_activities import (
    CASES,
    activities_for,
    activity_key,
    public_activity,
)


def _text(value):
    return "".join(char for char in unicodedata.normalize("NFKD", str(value).lower()) if not unicodedata.combining(char))


# Specific subjects precede broad products so a firewall or cleaning module does
# not receive a generic programming exercise just because its area is technology.
TOPICS = [
    ("firewall", ("firewall", "cortafuegos"), "Configura reglas de Azure Firewall", ["Definir tráfico permitido y denegado", "Crear reglas con el menor acceso necesario", "Probar conexiones permitidas y bloqueadas", "Revisar registros antes de publicar la configuración"], [("Regla de red", "Filtra por dirección, puerto y protocolo"), ("Regla de aplicación", "Restringe destinos de aplicación"), ("Registro", "Permite revisar conexiones y bloqueos"), ("Denegación por defecto", "Bloquea tráfico sin permiso explícito"), ("Mínimo privilegio", "Autoriza únicamente el acceso necesario")], "conexiones de prueba", "no cumplen las reglas autorizadas", "usan un puerto no autorizado"),
    ("invoice-ai", ("factur*", "invoice*"), "Revisa una extracción de facturas con IA", ["Definir los campos de las facturas", "Extraer campos y registrar la confianza", "Enviar datos dudosos a revisión humana", "Comparar la extracción con las facturas originales"], [("Extracción", "Obtiene campos desde un documento"), ("Confianza", "Indica incertidumbre del resultado del modelo"), ("Revisión humana", "Comprueba resultados dudosos con el original"), ("Validación", "Contrasta campos con criterios definidos"), ("Dato personal", "Requiere acceso y conservación limitados")], "facturas", "no tienen el importe requerido", "no tienen fecha válida"),
    ("privacy", ("privacidad", "privacy", "proteccion de datos", "datos personales"), "Revisa el uso de datos personales", ["Definir la finalidad del tratamiento", "Identificar los datos mínimos y la autorización", "Restringir acceso y conservación", "Comprobar el cumplimiento antes de compartir"], [("Finalidad", "Explica para qué se usarán los datos"), ("Minimización", "Limita la recogida a datos necesarios"), ("Autorización", "Habilita el tratamiento dentro de su alcance"), ("Conservación", "Define cuánto tiempo se guardan los datos"), ("Acceso", "Limita quién puede consultar información")], "solicitudes de datos", "no tienen autorización suficiente", "no indican una finalidad válida"),
    ("risk", ("riesgo*", "risk*"), "Prioriza riesgos y controles", ["Identificar activos y situaciones de riesgo", "Estimar probabilidad e impacto", "Asignar controles y responsables", "Revisar riesgo residual y seguimiento"], [("Probabilidad", "Estima la posibilidad de que ocurra un evento"), ("Impacto", "Describe las consecuencias del evento"), ("Control", "Reduce la probabilidad o las consecuencias"), ("Riesgo residual", "Permanece después de aplicar controles"), ("Responsable", "Da seguimiento al tratamiento acordado")], "controles", "no tienen responsable", "no tienen evidencia de ejecución"),
    ("data-cleaning", ("power query", "limpiar", "limpieza", "transformar", "etl"), "Limpia y comprueba una tabla", ["Revisar columnas y calidad en el origen", "Definir tipos y tratar valores ausentes", "Eliminar duplicados con una clave acordada", "Validar totales antes de cargar los datos"], [("Tipo de datos", "Determina cómo interpretar cada valor"), ("Valor nulo", "Representa un dato ausente"), ("Duplicado", "Repite una clave que debía ser única"), ("Paso aplicado", "Registra una transformación reproducible"), ("Perfil de columna", "Ayuda a detectar calidad y distribución de datos")], "filas", "no tienen fecha válida", "no tienen identificador válido"),
    ("power-bi", ("power bi", "power-bi", "dax", "visualiz*", "analisis de datos"), "Construye y valida un informe de Power BI", CASES["microsoft-data-analytics"][2], list(zip(CASES["microsoft-data-analytics"][5], CASES["microsoft-data-analytics"][6], strict=True)), "filas de ventas", "no tienen fecha válida", "no tienen importe válido"),
    ("excel", ("excel", "hoja de calculo"), "Comprueba una hoja de cálculo", ["Definir las columnas y el resultado esperado", "Revisar tipos de celda y referencias", "Aplicar fórmulas al rango acordado", "Comprobar resultados con datos de prueba"], [("Fórmula", "Calcula un resultado a partir de valores"), ("Referencia absoluta", "Conserva fija una referencia al copiar"), ("Filtro", "Muestra las filas que cumplen una condición"), ("Rango", "Agrupa las celdas de una operación"), ("Validación de datos", "Restringe las entradas permitidas en una celda")], "filas de la hoja", "no tienen el importe requerido", "no tienen una categoría válida"),
    ("word", ("word", "documento de texto"), "Prepara un documento accesible en Word", ["Definir estructura y audiencia del documento", "Aplicar estilos de título y texto", "Revisar navegación y accesibilidad", "Comprobar el documento antes de compartirlo"], [("Estilo", "Aplica formato coherente con una función"), ("Título", "Define la jerarquía de secciones"), ("Texto alternativo", "Describe el contenido relevante de una imagen"), ("Tabla de contenido", "Facilita navegar entre títulos"), ("Revisión", "Permite resolver cambios y comentarios")], "secciones del documento", "carecen del estilo de título requerido", "contienen una imagen sin texto alternativo requerido"),
    ("sql", ("sql", "consulta", "base de datos"), "Comprueba una consulta SQL", CASES["project-sql"][2], list(zip(CASES["project-sql"][5], CASES["project-sql"][6], strict=True)), "pedidos", "no tienen cliente válido", "no tienen importe válido"),
    ("git", ("git", "control de versiones"), "Prepara un cambio con Git", CASES["project-git"][2], list(zip(CASES["project-git"][5], CASES["project-git"][6], strict=True)), "comprobaciones del cambio", "fallan en la validación de entradas", "fallan en la comprobación de permisos"),
    ("python", ("python", "programacion"), "Valida datos con Python", CASES["technology"][2], list(zip(CASES["technology"][5], CASES["technology"][6], strict=True)), "registros", "no tienen identificador válido", "no tienen importe válido"),
    ("azure", ("azure", "nube", "cloud"), "Revisa una configuración de servicios en la nube", ["Definir necesidad y límites del servicio", "Elegir recursos y permisos mínimos", "Probar funcionamiento y acceso", "Comprobar consumo y registrar la configuración"], [("Recurso", "Representa un servicio desplegado"), ("Rol", "Agrupa permisos sobre un alcance"), ("Monitorización", "Permite observar funcionamiento y consumo"), ("Escalado", "Ajusta capacidad según la demanda"), ("Presupuesto", "Ayuda a seguir el consumo previsto")], "recursos", "no tienen el rol de acceso aprobado", "no tienen el presupuesto requerido"),
    ("ai", ("inteligencia artificial", "machine learning", " ai ", "modelo de ia"), "Comprueba resultados de un modelo de IA", ["Definir tarea y criterio de aceptación", "Separar datos de aprendizaje y prueba", "Comparar predicciones con referencias", "Documentar errores y límites de uso"], [("Predicción", "Es una salida del modelo para una entrada"), ("Conjunto de prueba", "Permite evaluar con datos apartados del aprendizaje"), ("Referencia", "Es el resultado esperado para comparar"), ("Sesgo", "Puede producir diferencias sistemáticas entre grupos"), ("Supervisión humana", "Permite revisar decisiones y límites de uso")], "predicciones", "no coinciden con la referencia", "incumplen el criterio de seguridad del caso"),
]


def legacy_practice(resource):
    key = activity_key(resource)
    case = CASES.get(key, CASES["general"])
    return {"lab_title": case[0], "lab_scenario": case[1], "activities": activities_for(key)}


def course_practice(resource):
    if not resource.get("url") and resource.get("kind") != "course":
        return legacy_practice(resource)
    details = resource.get("details") or {}
    # Match the title/actual syllabus first, then skills and description. A broad
    # skill on a resource must not override its more specific subject matter.
    title_text = _text(resource.get("title", ""))
    syllabus_text = _text(" ".join(details.get("syllabus") or []))
    secondary = _text(" ".join([*(resource.get("skills") or []), resource.get("instructions", "")]))
    topic = next((item for text in (title_text, syllabus_text, secondary) for item in TOPICS if any(re.search(r"(?<!\w)" + re.escape(token.strip().rstrip("*")) + ("" if token.endswith("*") else r"(?!\w)"), text) for token in item[1])), None)
    raw_level = details.get("level", "any")
    level = raw_level if raw_level in {"beginner", "intermediate", "advanced"} else "beginner"
    rank = {"beginner": 0, "intermediate": 1, "advanced": 2}[level]
    raw_hours = resource.get("hours")
    hours = float(raw_hours) if isinstance(raw_hours, (int, float)) and math.isfinite(raw_hours) and raw_hours > 0 else 1
    extent = 0 if hours < 2 else 1 if hours < 6 else 2
    total = [20, 40, 80][extent]
    count = min(6, 4 + max(rank, extent))
    if topic:
        key, _, title, sequence, concepts, unit, reason_a, reason_b = topic
        mode = "topic"
    else:
        case = CASES.get(resource.get("category"), CASES["general"])
        key, title, sequence = resource.get("category", "general"), case[0], case[2]
        concepts = list(zip(case[5], case[6], strict=True))
        unit, reason_a, reason_b = "entregas del caso", "no cumplen el criterio de contenido", "no cumplen el criterio de revisión"
        mode = "area_transfer"
    sequence = [*sequence[:-1], *["Documentar las decisiones antes de la comprobación final", "Revisar el alcance de las decisiones documentadas"][:count - 4], sequence[-1]]
    concepts = [*concepts, ("Criterio de aceptación", "Define una condición comprobable del resultado"), ("Trazabilidad", "Permite seguir decisiones y cambios con sus soportes")][:3 + max(rank, extent)]
    bad, other, overlap = total // 5, total // 10, total // 20
    common = f"Se revisan {total} {unit}: {bad} {reason_a} y {other} {reason_b}."
    if rank == 2:
        prompt = f"{common} Hay {overlap} que presentan ambos problemas. ¿Qué porcentaje cumple los dos criterios?"
        answer = (total - bad - other + overlap) / total * 100
        explanation = f"Evita contar dos veces la intersección: ({total} − {bad} − {other} + {overlap}) / {total} × 100 = {answer:g}%."
    elif rank == 1:
        prompt = f"{common} Son grupos distintos, sin solapamiento. ¿Qué porcentaje cumple los dos criterios?"
        answer = (total - bad - other) / total * 100
        explanation = f"Excluye ambos grupos y calcula la proporción: ({total} − {bad} − {other}) / {total} × 100 = {answer:g}%."
    else:
        prompt = f"{common} Son grupos distintos, sin solapamiento. ¿Cuántos cumplen los dos criterios?"
        answer = total - bad - other
        explanation = f"Resta los dos grupos que no cumplen: {total} − {bad} − {other} = {answer:g}."
    order = [*range(2, len(sequence)), 0, 1]
    meanings = [meaning for _, meaning in concepts]
    choices = [*meanings[1:], meanings[0]]
    minutes = min(45, 8 + 5 * rank + 7 * extent)
    scope = "Ejercicio local sobre el tema identificado en la ficha." if topic else "Ejercicio de transferencia al área; la ficha no permite identificar un tema específico con suficiente precisión."
    return {"lab_title": title, "lab_scenario": f"Aplica lo aprendido en «{resource.get('title', 'este curso')}». {scope} Usa los datos ficticios y criterios que se indican en cada actividad.",
            "adaptation": {"topic": key, "mode": mode, "level": level, "source_level": raw_level, "source_hours": raw_hours,
                           "minutes": minutes, "sequence_items": len(sequence), "concepts": len(concepts), "syllabus": (details.get("syllabus") or [])[:8]},
            "activities": [
                {"id": "sequence", "type": "order", "prompt": "Organiza el flujo de trabajo del caso, de principio a fin.", "choices": [sequence[index] for index in order], "answer": [order.index(index) for index in range(len(sequence))], "feedback": " → ".join(sequence)},
                {"id": "calculation", "type": "number", "prompt": prompt, "choices": [], "answer": answer, "feedback": explanation},
                {"id": "connections", "type": "matching", "prompt": "Relaciona los conceptos con su función en este caso.", "terms": [term for term, _ in concepts], "choices": choices, "answer": [choices.index(meaning) for meaning in meanings], "feedback": "; ".join(f"{term}: {meaning}" for term, meaning in concepts)},
            ]}


def practice_for_plan(resource, progress):
    if progress.get("practice_spec"):
        return deepcopy(progress["practice_spec"])
    # Do not reinterpret answers already saved with the previous sector bank.
    if progress.get("activity_answers") or progress.get("activity_feedback"):
        return legacy_practice(resource)
    return course_practice(resource)


def public_practice(practice):
    return {**practice, "activities": [public_activity(item) for item in practice["activities"]]}
