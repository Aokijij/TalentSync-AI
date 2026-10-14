"""Generate an editable, local rewrite from the candidate's actual words.

This is a conservative language generator, not a remote language model. It
changes presentation, never supplies achievements, tools or numbers.
"""
import re

from app.domain.services.skill_context import fold

# Anchored phrases keep qualifications such as "apoyo" and negation intact.
OPENINGS = (
    (r"gestión y control de\s+", "Gestioné y controlé ", "Gestiono y controlo "),
    (r"análisis y seguimiento de\s+", "Analicé y di seguimiento a ", "Analizo y doy seguimiento a "),
    (r"gestión de\s+", "Gestioné ", "Gestiono "),
    (r"control de\s+", "Controlé ", "Controlo "),
    (r"análisis de\s+", "Analicé ", "Analizo "),
    (r"seguimiento de\s+", "Di seguimiento a ", "Doy seguimiento a "),
    (r"elaboración de\s+", "Elaboré ", "Elaboro "),
    (r"validación de\s+", "Validé ", "Valido "),
    (r"preparación de\s+", "Preparé ", "Preparo "),
    (r"realización de\s+", "Realicé ", "Realizo "),
    (r"desarrollo de\s+", "Desarrollé ", "Desarrollo "),
    (r"diseño de\s+", "Diseñé ", "Diseño "),
    (r"atención a\s+", "Atendí a ", "Atiendo a "),
    (r"atención al\s+", "Atendí al ", "Atiendo al "),
    (r"apoyo en\s+", "Apoyé en ", "Apoyo en "),
    (r"participación en\s+", "Participé en ", "Participo en "),
    (r"responsable de\s+", "Fui responsable de ", "Soy responsable de "),
    (r"(?:yo\s+)?(?:hacía|hacia)\s+(?=(?:reportes|informes)\b)", "Elaboré ", "Elaboro "),
    (r"(?:yo\s+)?preparaba\s+", "Preparé ", "Preparo "),
    (r"(?:yo\s+)?elaboraba\s+", "Elaboré ", "Elaboro "),
    (r"(?:yo\s+)?realizaba\s+", "Realicé ", "Realizo "),
    (r"(?:yo\s+)?gestionaba\s+", "Gestioné ", "Gestiono "),
    (r"(?:yo\s+)?atendía\s+", "Atendí ", "Atiendo "),
    (r"(?:yo\s+)?apoyaba\s+", "Apoyé ", "Apoyo "),
    (r"fui (?:el|la) encargad[oa] de\s+", "Me encargué de ", "Me encargo de "),
)


def rewrite_experience(record, *, style="paragraph", result=""):
    original = str(record.get("description") or "").strip()
    if not original:
        raise ValueError("Escribe primero una frase sobre lo que hiciste en esta experiencia")
    result = result.strip()
    if re.search(r"\[[^\]]+\]", result):
        raise ValueError("Sustituye los marcadores del resultado por información real")
    current = record.get("is_current") is True or fold(record.get("end_year")) in {"presente", "actualidad", "actual"}
    # Imported PDFs sometimes concatenate separate responsibilities.
    source = re.sub(r"(?<=[a-záéíóúñ0-9])\s+(?=(?:Gestión|Análisis|Elaboración|Validación|Preparación|Atención|Apoyo|Participación)\b)", "\n", original)
    parts = re.split(r"\n+|;\s*|(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])", source)
    sentences, seen = [], set()
    transformed = False
    for position, part in enumerate([*parts, result]):
        text = re.sub(r"^[\s•*\-]+", "", part).strip()
        if not text or fold(text) in seen:
            continue
        seen.add(fold(text))
        # An optional result remains exactly what the person supplied.
        if position < len(parts):
            for pattern, past, present in OPENINGS:
                match = re.match(pattern, text, flags=re.I)
                if match:
                    text = (present if current else past) + text[match.end():]
                    transformed = True
                    break
        sentences.append(text if text[-1] in ".!?" else text + ".")
    if not sentences:
        raise ValueError("Añade una frase sobre lo que hiciste en esta experiencia")
    text = ("\n".join("• " + sentence for sentence in sentences) if style == "bullets" else " ".join(sentences))
    if len(text) > 3000:
        raise ValueError("La propuesta es demasiado larga; acorta la descripción o el resultado adicional")
    changes = ["Organicé el texto en ideas separadas."]
    if transformed:
        changes.append("Convertí responsabilidades en acciones sin añadir hechos.")
    if result:
        changes.append("Incluí el resultado que aportaste.")
    return {"text": text, "method": "local", "changes": changes,
            "questions": [] if result else ["Si recuerdas un resultado real, puedes añadirlo: ¿qué entregaste o qué cambió gracias a tu trabajo?"]}
