"""Explainable writing and consistency advice; never a hiring score."""
import re

from app.domain.services.experience_dates import month_index
from app.domain.services.skill_context import fold


def career_guidance(profile):
    advice = []
    experiences = getattr(profile, "experiences", None) or []
    studies = getattr(profile, "educations", None) or []
    skills = getattr(profile, "skills", None) or []
    source = (getattr(profile, "preferences", None) or {}).get("cv_source_text", "")

    def add(identity, title, detail, target, *, priority=2, original=None, index=None, writing=False):
        advice.append({"id": identity, "title": title, "detail": detail, "target": target,
                       "priority": priority, "original": original, "experience_index": index, "writing": writing})

    if not str(getattr(profile, "profession", "") or "").strip():
        add("profession", "Define el cargo o área que buscas", "Usa un título concreto y fiel a tu trayectoria para que se entienda tu objetivo profesional.", "profile-profession", priority=1)
    if not skills:
        add("skills", "Selecciona tus habilidades relevantes", "Añade las que puedas explicar con una experiencia, un proyecto o una práctica. No necesitas incluir todas las tecnologías que has visto.", "profile-skills", priority=1)
    if not experiences:
        add("first-example", "Muestra un ejemplo de lo que sabes hacer", "Puedes aportar un proyecto, una práctica o un entregable en tus evidencias. No necesitas convertir una actividad académica en un empleo.", "profile-evidence")
    for index, item in enumerate(experiences[:30]):
        role = str(item.get("role") or "Esta experiencia")
        description = str(item.get("description") or "").strip()
        if not description or not re.search(r"\b(?:reduj\w*|aument\w*|mejor\w*|logr\w*|permit\w*|ahorr\w*|entreg\w*|result\w*|cumpl\w*|reduc\w*|improv\w*|deliver\w*)\b|\d", fold(description)):
            add(f"impact-{index}", f"Explica tu aporte: {role}", "Describe el reto, qué hiciste y qué cambió gracias a tu trabajo. Si no tienes cifras comprobables, usa un resultado cualitativo o un entregable real.", f"experience-description-{index}", priority=1, original=description, index=index, writing=True)
        elif len(description.split()) > 110:
            add(f"concise-{index}", f"Haz más fácil de leer: {role}", "Esta descripción supera 110 palabras. Prueba con tres aportes breves: acción, herramienta o método y resultado. Conserva los hechos relevantes.", f"experience-description-{index}", original=description, index=index, writing=True)
        if not item.get("company") or not item.get("role"):
            add(f"identity-{index}", "Completa el cargo y la organización", "Revisa este registro importado antes de guardarlo: debe quedar claro dónde y en qué función participaste.", "profile-experiences", priority=1)
        if item.get("date_review_required") or month_index(item.get("start_date")) is None or not item.get("is_current") and month_index(item.get("end_date")) is None:
            add(f"dates-{index}", f"Precisa las fechas: {role}", "Completa mes y año si los conoces. Una fecha incompleta no demuestra falta de experiencia y no debe convertirse automáticamente en trabajo actual.", "profile-experiences")
    if sum(item.get("is_current") is True for item in experiences) > 1:
        add("current-jobs", "Revisa cuál es tu trabajo actual", "Hay varios empleos marcados como actuales. Selecciona el que corresponde y revisa las fechas de los anteriores.", "profile-experiences", priority=1)
    if studies and any(not item.get("degree") or not item.get("institution") for item in studies):
        add("education", "Completa los datos de tu formación", "Revisa título o carrera e institución. Marca «Actualmente estudiando» solo cuando corresponda.", "profile-educations")
    if len(skills) > 25:
        add("focused-skills", "Prioriza las habilidades que puedes respaldar", f"Tienes {len(skills)} habilidades declaradas. Revisa cuáles representan mejor tu objetivo y añade ejemplos de uso. Tener más etiquetas no demuestra mayor dominio.", "profile-skills")
    summary = str(getattr(profile, "experience", "") or "")
    if len(summary.split()) > 80:
        add("summary", "Enfoca tu presentación profesional", "El resumen supera 80 palabras. Revisa el cargo objetivo y las habilidades más relevantes; el resumen se reconstruye al guardar esos campos.", "profile-profession")
    emails = set(re.findall(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", source.casefold()))
    if len(emails) > 1:
        add("contact", "Revisa el contacto principal de tu PDF", f"El texto del PDF contiene {len(emails)} correos distintos. Comprueba cuáles quieres usar y unifica el contacto en el documento original.", "profile-contact")
    # Gaps are optional context, never a penalty. Only complete month dates qualify.
    periods = sorted((start, end) for item in experiences if (start := month_index(item.get("start_date"))) is not None and (end := month_index(item.get("end_date"))) is not None and end >= start)
    if periods:
        end = periods[0][1]
        gap = 0
        for start, stop in periods[1:]:
            gap = max(gap, start - end - 1)
            end = max(end, stop)
        if gap >= 6:
            add("timeline", "Comprueba la continuidad de las fechas", f"Entre registros con fechas completas hay un intervalo de {gap} meses. Comprueba si falta una experiencia. Añadir contexto personal es opcional; el intervalo no reduce tu compatibilidad.", "profile-experiences", priority=3)
    advice.sort(key=lambda item: item["priority"])
    if not advice:
        add("next-evidence", "Prepara una evidencia para tu próxima entrevista", "Elige un aporte real de tu trayectoria y prepara un ejemplo que explique qué hiciste y qué resultado obtuviste.", "profile-evidence", priority=3)
    return {"method": "profile-coach-rules-v1", "basis": "Último perfil guardado y texto disponible del PDF. Recomendaciones de claridad, no una evaluación de empleabilidad.",
            "items": advice, "total": len(advice), "source_available": bool(source)}
