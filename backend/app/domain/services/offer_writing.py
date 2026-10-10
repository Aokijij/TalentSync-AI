"""Local writing from supplied facts; no provider calls or invented conditions."""
from app.domain.services.offer_review import details_for

LEVELS = {"entry": "Inicial", "junior": "Junior", "mid": "Intermedio", "senior": "Senior", "lead": "Liderazgo"}


def writing_draft(job):
    details = details_for(job)
    proposals, questions = [], []
    missions = [row for row in details.get("missions", []) if row.get("outcome", "").strip() and row.get("measure", "").strip()]
    if missions:
        lines = [f"Resultados esperados para el cargo {job.title.strip() or 'por definir'}:"]
        for row in missions:
            lines.append(f"• En {row.get('days', 90)} días: {row['outcome'].strip()}. Evaluación: {row['measure'].strip()}.")
        if details.get("schedule"):
            lines.append(f"Jornada y horario: {details['schedule'].strip()}.")
        proposals.append({"field": "description", "label": "Responsabilidades orientadas a resultados", "step": 1,
                          "original": job.description or "", "text": "\n".join(lines),
                          "basis": "Misiones, criterios de evaluación, plazos y horario que registraste. Revisa y conserva cualquier contexto adicional necesario."})
    else:
        questions.append({"step": 1, "text": "¿Qué entregará esta persona en sus primeros 90 días y con qué criterio comprobarán el resultado? Completa una misión y su evaluación para preparar la redacción."})
    skills = getattr(job, "skill_requirements", None) or []
    essential = [row["skill"] for row in skills if row.get("essential")]
    desirable = [row["skill"] for row in skills if not row.get("essential")]
    learnable = details.get("learnable_skills", [])
    requirements = []
    if details.get("seniority"):
        requirements.append(f"Nivel del cargo: {LEVELS.get(details['seniority'], details['seniority'])}.")
    years = details.get("experience_years")
    if years is not None:
        requirements.append("No se exige experiencia laboral previa." if years == 0 else f"Experiencia requerida: {years} {'año' if years == 1 else 'años'}.")
    for label, values in [("Habilidades esenciales al ingreso", essential), ("Habilidades deseables", desirable), ("Habilidades que pueden aprenderse durante el ingreso", learnable)]:
        if values:
            requirements.append(f"{label}: {', '.join(values)}.")
    if requirements:
        proposals.append({"field": "requirements", "label": "Requisitos separados por prioridad", "step": 2,
                          "original": job.requirements or "", "text": "\n".join(requirements),
                          "basis": "Nivel, experiencia y habilidades configuradas. Añade formación, idiomas y evidencias exigidas que todavía no estén descritos."})
    if not essential:
        questions.append({"step": 2, "text": "¿Qué habilidad debe demostrar al ingresar y cuáles puede aprender con acompañamiento? Marca las esenciales antes de publicar."})
    if years is None:
        questions.append({"step": 2, "text": "¿Cuánta experiencia requiere el alcance real del cargo? Define el nivel y los años sin confundirlos con la edad de la persona."})
    return {"method": "local-structured-writing-v1", "proposals": proposals, "questions": questions,
            "notice": "Borradores preparados localmente con tus datos. Puedes editarlos antes de aplicarlos; no se guardan ni publican automáticamente."}
