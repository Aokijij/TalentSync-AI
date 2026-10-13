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
    "microservicios": ["microservices"], ".net": ["dotnet"],
}
NEGATED = r"\b(?:no|nunca|sin|not|never|without|lack|don't|do not)\s+(?:(?:tengo|cuento con|poseo|he|haber|have|having|any|tiene|tienen)\s+)?(?:experiencia|conocimientos?|dominio|manejo|experience|knowledge|used|usado|utilizado|trabajado|uso|manejo|conozco|domino|know)\b"
LEARNING = r"\b(?:aprendiendo|estudiando|en aprendizaje|en formacion|learning|studying|curso de|curso en|formacion en|fundamentos de|introduccion a|basico en|basica en|beginner|familiarizandome con)\b"
APPLIED = r"\b(?:desarroll\w*|implement\w*|utili[cz]\w*|trabaj\w*|constru\w*|automat\w*|administr\w*|analic\w*|gestion\w*|programe|programo|programado|built|developed|implemented|worked|used|uso|use|experiencia en|experience with)\b"


def skill_mentions(text, skills, aliases=None):
    """No inferred skills: each result must contain a literal skill or alias.

    Clause boundaries stop a negative or learning statement spilling into the
    next positive statement. These are language rules, not calibrated confidence.
    """
    source = str(text or "")[:30000]
    clauses = re.split(r"[\n;!?]|\.(?=\s+[A-ZÁÉÍÓÚ]|$)|\b(?:pero|but|sin embargo)\b|\by\s+(?=(?:uso|utilizo|desarroll|trabaj|implement))", source, flags=re.I)
    headings = [(match.start(), match[1]) for match in re.finditer(r"^[\s#*]*(cursos|certificaciones|formacion(?: academica)?|educacion|estudios|education|courses|certifications|proyectos|portafolio|projects|experiencia(?: laboral| profesional)?|work experience|habilidades|skills|perfil|resumen|idiomas)[\s:*]*$", fold(source), flags=re.M)]
    result = []
    for skill in dict.fromkeys(skill_key(item) for item in skills):
        cursor = 0
        terms = [skill, *VARIANTS.get(skill, [])]
        patterns = [r"(?<![\w+#])(?:" + "|".join(re.escape(fold(term)).replace(r"\ ", r"\s+") for term in terms) + r")(?![\w+#])", *((aliases or {}).get(skill, []))]
        pattern = "|".join(f"(?:{item})" for item in patterns)
        for clause in clauses:
            offset = source.find(clause, cursor)
            cursor = max(cursor, offset + len(clause))
            heading = next((label for position, label in reversed(headings) if position <= offset), "")
            section = "project" if heading in {"proyectos", "portafolio", "projects"} else "learning" if heading in {"cursos", "certificaciones", "formacion", "formacion academica", "educacion", "estudios", "education", "courses", "certifications"} else "professional"
            value = fold(clause)
            for match in re.finditer(pattern, value):
                before, after = value[max(0, match.start() - 110):match.start()], value[match.end():match.end() + 55]
                suffix = after if re.match(r"\s*[:(—-]", after) else ""
                state = "negated" if re.search(NEGATED, before + suffix) else "learning" if re.search(LEARNING, before + suffix) else "applied" if re.search(APPLIED, before) else "declared"
                if section in {"project", "learning"} and state != "negated":
                    state = section
                result.append({"skill": skill, "state": state, "excerpt": clause.strip()[:240], "source_section": section})
    return result[:300]


def extraction_context(text, skills, experiences, aliases=None):
    rows = skill_mentions(text, skills, aliases=aliases)
    for row in rows:
        row["experience_indexes"] = [index for index, entry in enumerate(experiences) if any(item["state"] in {"applied", "declared"} for item in skill_mentions(f"{entry.get('role', '')}. {entry.get('description', '')}", [row["skill"]], aliases=aliases))]
    return rows
