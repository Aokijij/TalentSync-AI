"""Local editorial assistance: preserve supplied context and structure explicit facts."""
import re

from app.domain.services.offer_review import details_for

LEVELS = {"entry": "Inicial", "junior": "Junior", "mid": "Intermedio", "senior": "Senior", "lead": "Liderazgo"}
VERBS = {"analizará": "Analizar", "revisará": "Revisar", "preparará": "Preparar", "gestionará": "Gestionar", "coordinará": "Coordinar", "registrará": "Registrar", "atenderá": "Atender", "desarrollará": "Desarrollar", "documentará": "Documentar", "verificará": "Verificar", "construirá": "Construir", "organizará": "Organizar", "diseñará": "Diseñar", "implementará": "Implementar", "mantendrá": "Mantener", "conciliará": "Conciliar"}
CLICHES = r"din[aá]mic[oa]|guerrer[oa]|tolerancia a la frustraci[oó]n|trabajo bajo presi[oó]n|proactiv[oa]"


def editorial_lines(text, *, responsibilities=False):
    lines, removed, rewritten = [], [], 0
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", str(text or "")):
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
                pattern = rf"\b{verb}\b"
                sentence, count = re.subn(pattern, lambda match: infinitive if match.start() == 0 else infinitive.lower(), sentence, flags=re.I)
                rewritten += count
        if sentence.casefold().rstrip(".") not in {line.casefold().rstrip(".") for line in lines}:
            lines.append(sentence)
    return lines, removed, rewritten


def writing_draft(job):
    details = details_for(job)
    proposals, questions = [], []
    missions = [row for row in details.get("missions", []) if row.get("outcome", "").strip() and row.get("measure", "").strip()]
    original_lines, removed, rewritten = editorial_lines(job.description, responsibilities=True)
    generated = {"responsabilidades y contexto", "resultados y evaluación", "condiciones registradas"}
    for row in missions:
        generated.add(f"en {row.get('days', 90)} días: {row['outcome'].strip().rstrip('.')}.".casefold())
        generated.add(f"cómo se comprobará: {row['measure'].strip().rstrip('.')}.".casefold())
    if details.get("schedule"):
        generated.add(f"jornada y horario: {details['schedule'].strip().rstrip('.')}.".casefold())
    modality = {"remote": "Remota", "hybrid": "Híbrida", "onsite": "Presencial"}.get(getattr(job, "modality", None))
    location = getattr(job, "location", None)
    if modality:
        generated.add(f"Modalidad: {modality}{' · ' + location.strip() if location else ''}.".casefold())
    original_lines = [line for line in original_lines if line.casefold() not in generated]
    if original_lines or missions:
        lines, changes = [], []
        if original_lines:
            lines += ["Responsabilidades y contexto", *[f"• {line}" for line in original_lines]]
            changes.append("Conserva el contexto y las condiciones descritas; presenta cada idea en una viñeta.")
        if rewritten:
            changes.append("Convierte las funciones en acciones directas para facilitar su lectura.")
        if missions:
            lines += ["", "Resultados y evaluación"]
            for row in missions:
                lines += [f"• En {row.get('days', 90)} días: {row['outcome'].strip().rstrip('.')}.", f"  Cómo se comprobará: {row['measure'].strip().rstrip('.')}." ]
            changes.append("Separa los entregables, sus plazos y el criterio que utilizará el equipo.")
        conditions = []
        if details.get("schedule"):
            conditions.append(f"Jornada y horario: {details['schedule'].strip().rstrip('.')}.")
        if modality:
            conditions.append(f"Modalidad: {modality}{' · ' + location.strip() if location else ''}.")
        if conditions:
            lines += ["", "Condiciones registradas", *conditions]
            changes.append("Agrupa la jornada y la modalidad registradas sin inventar nuevas condiciones.")
        if removed:
            changes.append("Retira frases genéricas independientes: " + "; ".join(f'«{phrase}»' for phrase in removed))
        proposals.append({"field": "description", "label": "Responsabilidades y resultados", "step": 1,
                          "original": job.description or "", "text": "\n".join(lines), "changes": changes,
                          "basis": "Texto actual, misiones y condiciones que registraste. Comprueba el resultado antes de aplicarlo."})
    if not missions:
        questions.append({"step": 1, "text": "¿Qué entregará esta persona y con qué criterio comprobarán el resultado? Completa una misión y su evaluación para enriquecer el texto."})
    skills = getattr(job, "skill_requirements", None) or []
    learnable = list(dict.fromkeys(details.get("learnable_skills", [])))
    learnable_keys = {value.strip().casefold() for value in learnable}
    essential = list(dict.fromkeys(row["skill"] for row in skills if row.get("essential")))
    desirable = list(dict.fromkeys(row["skill"] for row in skills if not row.get("essential") and row["skill"].strip().casefold() not in learnable_keys))
    requirements, changes = [], []
    if details.get("seniority"):
        requirements.append(f"Nivel del cargo: {LEVELS.get(details['seniority'], details['seniority'])}.")
    years = details.get("experience_years")
    if years is not None:
        requirements.append("No se exige experiencia laboral previa." if years == 0 else f"Experiencia requerida: {years} {'año' if years == 1 else 'años'}.")
    for label, values in [("Esencial al ingresar", essential), ("Deseable, no imprescindible", desirable), ("Puedes aprender durante el ingreso", learnable)]:
        if values:
            requirements += ["", label, *[f"• {value}" for value in values]]
    if skills or learnable:
        changes.append("Distingue lo esencial, lo deseable y lo que puede aprenderse; evita repetir una habilidad aprendible como exigencia deseable.")
    languages = getattr(job, "languages", None) or []
    if languages:
        requirements += ["", "Idiomas solicitados", *[f"• {row['name']}: nivel mínimo {row['level'] if row['level'] != 'NATIVE' else 'nativo'}." for row in languages]]
        changes.append("Incluye los idiomas y niveles mínimos configurados.")
    original_requirements, removed_requirements, _ = editorial_lines(job.requirements)
    generated_requirements = {line.casefold().strip(" •") for line in requirements if line}
    generated_requirements.add("conocimientos y evidencias aceptadas")
    original_requirements = [line for line in original_requirements if line.casefold() not in generated_requirements]
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
        questions.append({"step": 2, "text": "¿Qué habilidad debe demostrar al ingresar y cuáles puede aprender con acompañamiento? Marca las esenciales antes de publicar."})
    if years is None:
        questions.append({"step": 2, "text": "¿Cuánta experiencia requiere el alcance real del cargo? Define el nivel y los años sin confundirlos con la edad de la persona."})
    elif any(int(value) != years for value in re.findall(r"(\d{1,2})\s*(?:años|years)", job.requirements or "", re.I)):
        questions.append({"step": 2, "text": "El texto actual y la experiencia configurada mencionan años diferentes. Confirma la condición correcta antes de aplicar la propuesta."})
    if set(value.casefold() for value in essential) & learnable_keys:
        questions.append({"step": 2, "text": "Una habilidad figura como esencial y aprendible. Decide si debe dominarla al ingresar o si recibirá formación."})
    return {"method": "local-editorial-writing-v2", "proposals": proposals, "questions": questions,
            "notice": "Revisión editorial local: organiza tus datos, conserva el contexto y retira frases genéricas independientes. Revisa los borradores; no se guardan ni publican automáticamente."}
