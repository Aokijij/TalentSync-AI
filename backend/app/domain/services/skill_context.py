"""Conservative, inspectable language context for explicitly mentioned skills."""
import re
import unicodedata

from app.domain.services.skills import skill_key


def fold(value):
    return "".join(char for char in unicodedata.normalize("NFKD", str(value or "").lower()) if not unicodedata.combining(char))


VARIANTS = {
    "javascript": ["js"], "typescript": ["ts"], "nodejs": ["node.js"],
    "postgresql": ["postgres"], "kubernetes": ["k8s"], "spring boot": ["springboot"],
    "api rest": ["rest api", "restful api"], "servicio al cliente": ["atención al cliente", "customer service"],
    "microservicios": ["microservices"], ".net": ["dotnet"], "html": ["html5"], "css": ["css3"],
}
NEGATED = r"\b(?:no|nunca|sin|not|never|without|lack|don't|do not)\s+(?:(?:tengo|cuento con|poseo|he|haber|have|having|any|tiene|tienen)\s+)?(?:experiencia|conocimientos?|dominio|manejo|experience|knowledge|used|usado|utilizado|trabajado|uso|manejo|conozco|domino|know)\b"
LEARNING = r"\b(?:aprendiendo|estudiando|en aprendizaje|familiarizandome con|(?:i am|i'm|am|currently|still) learning|learning to use)\b"
TRAINING = r"\b(?:curso(?:s)?(?: de| en|:)|formacion (?:en|de)|fundamentos de|introduccion a|course (?:in|on))\b"
APPLIED = r"\b(?:desarroll\w*|implement\w*|utili[cz]\w*|trabaj\w*|constru\w*|automat\w*|administr\w*|analic\w*|gestion\w*|programe|programo|programado|built|developed|implemented|worked|used|uso|use|experiencia en|experience with)\b"
CONTEXT_VERSION = "skill-context-v2"
HEADINGS = {
    "training": {"cursos", "certificaciones", "formacion", "formacion academica", "educacion", "estudios", "education", "courses", "certifications"},
    "project": {"proyectos", "portafolio", "projects"},
    "professional": {"experiencia", "experiencia laboral", "experiencia profesional", "work experience", "habilidades", "skills", "tecnologias", "competencias", "competencias tecnicas", "conocimientos", "perfil", "perfil profesional", "resumen", "contacto", "contact", "idiomas", "languages"},
    "unknown": {"tecnologias proyectos", "educacion experiencia", "educacion y experiencia"},
}


def _fold_offsets(text):
    chars, offsets = [], []
    for index, char in enumerate(text):
        for folded in fold(char):
            chars.append(folded)
            offsets.append(index)
    return "".join(chars), offsets


def skill_mentions(text, skills, aliases=None):
    """A section indicates provenance, never whether somebody is learning now."""
    source = str(text or "")[:30000]
    headings = []
    for line in re.finditer(r"[^\n]+", source):
        label = fold(line[0]).strip(" \t#*:—-")
        for section, names in HEADINGS.items():
            if label in names:
                headings.append((line.start(), section, line[0].strip()))
                break
    separators = r"[\n;!?]|\.(?=\s+[A-ZÁÉÍÓÚ]|$)|\b(?:pero|but|sin embargo)\b|(?:,|\by)\s+(?=(?:uso|utilizo|domino|manejo|desarroll|trabaj|implement|estoy|sigo|i use|i am))"
    clauses, start = [], 0
    for boundary in re.finditer(separators, source, flags=re.I):
        clauses.append((start, source[start:boundary.start()]))
        start = boundary.end()
    clauses.append((start, source[start:]))
    result = []
    for skill in dict.fromkeys(skill_key(item) for item in skills):
        if not skill:
            continue
        terms = [skill, *VARIANTS.get(skill, [])]
        patterns = [r"(?<![\w+#])(?:" + "|".join(re.escape(fold(term)).replace(r"\ ", r"\s+") for term in terms) + r")(?![\w+#])", *((aliases or {}).get(skill, []))]
        pattern = "|".join(f"(?:{item})" for item in patterns)
        for offset, clause in clauses:
            if not clause.strip():
                continue
            section, heading = next(((kind, title) for position, kind, title in reversed(headings) if position <= offset), ("professional", ""))
            value, positions = _fold_offsets(clause)
            for match in re.finditer(pattern, value):
                before, after = value[max(0, match.start() - 110):match.start()], value[match.end():match.end() + 55]
                suffix = after if re.match(r"\s*[:(—-]", after) else ""
                scope = before + suffix
                negative, learning = re.search(NEGATED, scope), re.search(LEARNING, scope)
                if learning and re.search(r"\b(?:no|not)\s+(?:\w+\s+){0,3}$", scope[:learning.start()]):
                    learning = None
                state, cue = "declared", ""
                reason = "La habilidad se menciona sin una declaración explícita de aprendizaje o falta de experiencia."
                if negative:
                    state, cue = "negated", negative[0]
                    reason = f"El fragmento contiene «{cue}» junto a esta habilidad."
                elif learning:
                    state, cue = "learning", learning[0]
                    reason = f"El fragmento contiene «{cue}» junto a esta habilidad."
                elif section == "project":
                    state, reason = "project", f"La mención está bajo «{heading}»; no se interpreta como experiencia laboral."
                elif section == "training" or re.search(TRAINING, scope):
                    state = "training"
                    reason = f"La mención está en formación{f' bajo «{heading}»' if heading else ''}. Esto no indica que sigas estudiándola ni acredita dominio."
                elif section == "unknown":
                    state, reason = "unknown", "El texto mezcla encabezados; no hay contexto suficiente para clasificar la mención."
                elif re.search(APPLIED, before):
                    state = "applied"
                    reason = "El fragmento menciona una acción o experiencia con esta habilidad."
                a, b = offset + positions[match.start()], offset + positions[match.end() - 1] + 1
                excerpt_start = max(0, positions[match.start()] - 110)
                result.append({"skill": skill, "state": state, "excerpt": clause[excerpt_start:excerpt_start + 240].strip(),
                               "source_section": section, "section_heading": heading, "reason": reason, "cue": cue,
                               "start": a, "end": b, "context_version": CONTEXT_VERSION})
    return result[:300]


def profile_skill_context(profile):
    """Reinterpret legacy rows without treating old section guesses as facts."""
    prefs = getattr(profile, "preferences", None) or {}
    rows = prefs.get("cv_skill_context", [])
    if prefs.get("cv_context_version") == CONTEXT_VERSION:
        return rows
    refreshed = []
    for row in rows[:300]:
        if row.get("context_version") == CONTEXT_VERSION:
            refreshed.append(row)
            continue
        mentions = skill_mentions(row.get("excerpt", ""), [row.get("skill", "")])
        for item in mentions:
            if row.get("state") == "learning" and not item["cue"]:
                item.update(state="unknown", reason="El análisis anterior usó el encabezado de formación, pero este fragmento no indica aprendizaje actual. Confirma el contexto.")
            elif row.get("state") == "project" and not item["cue"]:
                item.update(state="project", reason="La importación anterior situó esta mención en proyectos; revisa el fragmento antes de declararla.")
            refreshed.append(item)
    return refreshed


def extraction_context(text, skills, experiences, aliases=None):
    rows = skill_mentions(text, skills, aliases=aliases)
    for row in rows:
        row["experience_indexes"] = [index for index, entry in enumerate(experiences) if any(item["state"] in {"applied", "declared"} for item in skill_mentions(f"{entry.get('role', '')}. {entry.get('description', '')}", [row["skill"]], aliases=aliases))]
    return rows
