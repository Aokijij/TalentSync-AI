"""Local editorial assistance: preserve supplied context and structure explicit facts."""
import re

from app.domain.services.job_requirements import (
    experience_label,
    minimum_experience_months,
)
from app.domain.services.offer_review import details_for

LEVELS = {"entry": "Inicial", "junior": "Junior", "mid": "Intermedio", "senior": "Senior", "lead": "Liderazgo"}
VERBS = {"analizará": "Analizar", "revisará": "Revisar", "preparará": "Preparar", "gestionará": "Gestionar", "coordinará": "Coordinar", "registrará": "Registrar", "atenderá": "Atender", "desarrollará": "Desarrollar", "documentará": "Documentar", "verificará": "Verificar", "construirá": "Construir", "organizará": "Organizar", "diseñará": "Diseñar", "implementará": "Implementar", "mantendrá": "Mantener", "conciliará": "Conciliar"}
EDUCATION = {"secondary": "Bachillerato", "technical": "Técnico", "technologist": "Tecnólogo", "university": "Profesional universitario", "postgraduate": "Posgrado"}


def line_key(value):
    return value.casefold().strip(" •-–.")


VERBS.update({"apoyará": "Apoyar", "evaluará": "Evaluar", "ejecutará": "Ejecutar", "validará": "Validar", "asesorará": "Asesorar", "supervisará": "Supervisar", "elaborará": "Elaborar", "operará": "Operar", "realizará": "Realizar", "participará": "Participar"})

CLICHES = r"din[aá]mic[oa]|guerrer[oa]|tolerancia a la frustraci[oó]n|trabajo bajo presi[oó]n|proactiv[oa]"


def editorial_lines(text, *, responsibilities=False):
    lines, removed, rewritten = [], [], 0
    sentences = re.split(r"(?<=[.!?])\s+|\n+|[•●]\s*|\s*;\s*", str(text or ""))
    if responsibilities:
        verbs = "|".join(verb.replace("á", "[aá]") for verb in VERBS)
        sentences = [part for sentence in sentences for part in re.split(rf"(?:,\s*|\s+y\s+)(?=(?:{verbs})\b)", sentence, flags=re.I)]
    for sentence in sentences:
        sentence = " ".join(sentence.split()).strip(" •-–")
        if not sentence:
            continue
        vague = re.search(CLICHES, sentence, re.I)
        has_action = re.search(r"\b(?:analiz|revis|prepar|gestion|coordin|registr|atend|desarroll|document|verific|constru|organiz|diseñ|implement|manten|concil)\w*", sentence, re.I)
        # Remove a generic standalone demand, never a sentence containing concrete facts.
        if vague and not has_action and not re.search(r"\d|certific|formaci[oó]n|horario|contrato|salario|idioma", sentence, re.I) and len(sentence) < 160:
            removed.append(sentence)
            continue
        if responsibilities:
            for verb, infinitive in VERBS.items():
                pattern = rf"\b{verb.replace('á', '[aá]')}\b"
                def action(match):
                    prefix = sentence[:match.start()].strip()
                    if not prefix:
                        return infinitive
                    return infinitive.lower() if re.search(r"(?:,|\by)\s*$", prefix) else match.group()
                previous = sentence
                sentence = re.sub(pattern, action, sentence, flags=re.I)
                rewritten += int(sentence != previous)
        sentence = sentence[0].upper() + sentence[1:]
        if sentence[-1] not in ".!?":
            sentence += "."
        if line_key(sentence) not in {line_key(line) for line in lines}:
            lines.append(sentence)
    return lines, removed, rewritten


def writing_draft(job):
    details = details_for(job)
    proposals, questions = [], []
    missions = [row for row in details.get("missions", []) if row.get("outcome", "").strip() and row.get("measure", "").strip()]
    original_lines, removed, rewritten = editorial_lines(job.description, responsibilities=True)
    generated = {"responsabilidades y contexto", "responsabilidades del cargo", "resultados y evaluación", "resultados esperados", "condiciones registradas"}
    for row in missions:
        generated.add(f"en {row.get('days', 90)} días: {row['outcome'].strip().rstrip('.')}.".casefold())
        generated.add(f"cómo se comprobará: {row['measure'].strip().rstrip('.')}.".casefold())
    if details.get("schedule"):
        generated.add(f"jornada y horario: {details['schedule'].strip().rstrip('.')}.".casefold())
    modality = {"remote": "Remota", "hybrid": "Híbrida", "onsite": "Presencial"}.get(getattr(job, "modality", None))
    location = getattr(job, "location", None)
    if modality:
        generated.add(f"Modalidad: {modality}{' · ' + location.strip() if location else ''}.".casefold())
    original_lines = [line for line in original_lines if line_key(line) not in {line_key(item) for item in generated}]
    if original_lines or missions:
        lines, changes = [], []
        if original_lines:
            lines += ["Responsabilidades del cargo", *[f"• {line}" for line in original_lines]]
            changes.append("Presenta las funciones y su contexto en ideas breves, con puntuación y sin repetirlas.")
        if rewritten:
            changes.append("Convierte las funciones en acciones directas para facilitar su lectura.")
        if missions:
            lines += ["", "Resultados esperados"]
            for row in missions:
                lines += [f"• En {row.get('days', 90)} días: {row['outcome'].strip().rstrip('.')}.", f"  Cómo se comprobará: {row['measure'].strip().rstrip('.')}." ]
            changes.append("Separa los entregables, sus plazos y el criterio que utilizará el equipo.")
        if details.get("schedule") or modality:
            changes.append("Deja el horario y la modalidad en Condiciones para evitar repetirlos en las funciones.")
        if removed:
            changes.append("Retira frases genéricas independientes: " + "; ".join(f'«{phrase}»' for phrase in removed))
        proposals.append({"field": "description", "label": "Responsabilidades y resultados", "step": 1,
                          "original": job.description or "", "text": "\n".join(lines), "changes": changes,
                          "basis": "Texto actual, misiones y condiciones que registraste. Comprueba el resultado antes de aplicarlo."})
    if not missions:
        questions.append({"step": 1, "text": "Si quieres añadir una misión, define qué resultado esperas y cómo lo revisará el equipo."})
    skills = getattr(job, "skill_requirements", None) or []
    learnable = list(dict.fromkeys(details.get("learnable_skills", [])))
    learnable_keys = {value.strip().casefold() for value in learnable}
    essential = list(dict.fromkeys(row["skill"] for row in skills if row.get("essential")))
    desirable = list(dict.fromkeys(row["skill"] for row in skills if not row.get("essential") and row["skill"].strip().casefold() not in learnable_keys))
    requirements, changes = [], []
    if details.get("seniority"):
        requirements.append(f"Nivel del cargo: {LEVELS.get(details['seniority'], details['seniority'])}.")
    months = minimum_experience_months(details)
    if months is not None:
        requirements.append("No se exige experiencia laboral previa." if months == 0 else f"Experiencia requerida: {experience_label(details)}.")
    level = getattr(job, "required_education_level", None)
    if level:
        status = "en formación o terminado" if level != "secondary" and details.get("education_accepts_in_progress") else "terminado"
        requirements.append(f"Formación: {EDUCATION.get(level, level)} · {status}.")
        fields = getattr(job, "required_study_fields", None) or []
        if fields and level != "secondary":
            requirements += ["", "Áreas de formación aceptadas", *[f"• {field}" for field in fields]]
            requirements.append("Se admiten solo estas áreas y sus variantes de nombre." if details.get("education_field_policy") == "exact" else "También se consideran formaciones afines con cumplimiento parcial y revisión de sus contenidos.")
        changes.append("Aclara la formación solicitada y si se aceptan personas que aún están estudiando.")
    for label, values in [("Esencial al ingresar", essential), ("Deseable, no imprescindible", desirable), ("Puedes aprender durante el ingreso", learnable)]:
        if values:
            requirements += ["", label, *[f"• {value}" for value in values]]
    if skills or learnable:
        changes.append("Distingue lo esencial, lo deseable y lo que puede aprenderse; evita repetir una habilidad aprendible como exigencia deseable.")
    credential_requirements = details.get("credential_requirements") or {}
    if credential_requirements.get("driving_categories"):
        requirements.append("Licencia de conducción vigente en alguna de estas categorías: " + ", ".join(credential_requirements["driving_categories"]) + ".")
    if credential_requirements.get("professional_cards"):
        requirements.append("Tarjeta profesional vigente para alguna de estas profesiones: " + ", ".join(credential_requirements["professional_cards"]) + ".")
    languages = getattr(job, "languages", None) or []
    if languages:
        requirements += ["", "Idiomas solicitados", *[f"• {row['name']}: nivel mínimo {row['level'] if row['level'] != 'NATIVE' else 'nativo'}." for row in languages]]
        changes.append("Incluye los idiomas y niveles mínimos configurados.")
    original_requirements, removed_requirements, _ = editorial_lines(job.requirements)
    generated_requirements = {line_key(line) for line in requirements if line}
    generated_requirements.add("conocimientos y evidencias aceptadas")
    original_requirements = [line for line in original_requirements if line_key(line) not in generated_requirements]
    if original_requirements:
        requirements += ["", "Conocimientos y evidencias aceptadas", *[f"• {line}" for line in original_requirements]]
        changes.append("Conserva la formación, evidencia y conocimientos explicados en el texto actual.")
    if removed_requirements:
        changes.append("Retira exigencias genéricas independientes: " + "; ".join(f'«{phrase}»' for phrase in removed_requirements))
    if requirements:
        proposals.append({"field": "requirements", "label": "Requisitos claros y priorizados", "step": 2,
                          "original": job.requirements or "", "text": "\n".join(requirements).strip(), "changes": changes,
                          "basis": "Preserva los conocimientos y evidencias del texto original y organiza las prioridades que configuraste."})
    if not essential:
        questions.append({"step": 2, "text": "¿Qué conocimientos hacen falta al ingresar y cuáles enseñará el equipo? Revisa la prioridad de las habilidades para reflejar esa diferencia."})
    if months is None:
        questions.append({"step": 2, "text": "¿Cuánta experiencia requiere el alcance real del cargo? Define el nivel y los meses o años sin confundirlos con la edad de la persona."})
    elif any(int(value) * (1 if unit.casefold().startswith("mes") else 12) != months for value, unit in re.findall(r"(\d{1,3})\s*(años?|years?|mes(?:es)?)", job.requirements or "", re.I)):
        questions.append({"step": 2, "text": "El texto actual y la experiencia configurada mencionan meses o años diferentes. Confirma la condición correcta antes de aplicar la propuesta."})
    if set(value.casefold() for value in essential) & learnable_keys:
        questions.append({"step": 2, "text": "Una habilidad figura como esencial y aprendible. Decide si debe dominarla al ingresar o si recibirá formación."})
    return {"method": "local-editorial-writing-v3", "proposals": proposals, "questions": questions,
            "notice": "Propuestas basadas en los datos de tu vacante: funciones concretas, requisitos ordenados y formación clara. Revisa y edita cada texto antes de aplicarlo al borrador."}
