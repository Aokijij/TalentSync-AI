"""Generate an editable, local rewrite from the candidate's actual words.

This is a conservative language generator, not a remote language model. It
changes presentation, never supplies achievements, tools or numbers.
"""
import re

from app.domain.services.skill_context import fold


def validate_generated_text(generated, record, result=""):
    if "actions" in generated:
        return validate_complete_rewrite(generated, record, result)
    text = str(generated.get("text") or "").strip()
    original = str(record.get("description") or "")
    source = fold(" ".join([original, str(record.get("role") or ""), result]))
    if not text or len(text) > 3000:
        raise ValueError("La propuesta no está completa. Inténtalo de nuevo")
    # Remove standalone promotional claims, keeping only the grounded draft.
    # A mixed sentence is discarded as a whole rather than reinterpreted.
    claims = ("lider", "dirig", "aument", "reduj", "optimiz", "mejor", "increment", "ahorr", "garanti", "eficien", "productividad", "alto nivel", "me esforc", "aporte significativo")
    sentences = re.split(r"\n+|(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])", text)
    supported = [sentence for sentence in sentences if not any(claim in fold(sentence) and claim not in source for claim in claims)]
    if not supported:
        raise ValueError("La propuesta añadió un resultado o una responsabilidad sin respaldo. No se guardó ningún cambio")
    text = ("\n" if "\n" in text else " ").join(supported)
    current = record.get("is_current") is True or fold(record.get("end_year")) in {"presente", "actualidad", "actual"}
    text = text.replace("Mi trabajo se centró en", "Mi trabajo se centra en") if current else text.replace("Mi trabajo se centra en", "Mi trabajo se centró en")
    if re.search(r"\b(?:no|nunca|sin)\b", fold(original)) and not re.search(r"\b(?:no|nunca|sin)\b", fold(text)):
        raise ValueError("La propuesta perdió una aclaración de tu texto. No se guardó ningún cambio")
    if any(value in fold(original) for value in ("apoy", "colabor", "particip")) and not any(value in fold(text) for value in ("apoy", "colabor", "particip")):
        raise ValueError("La propuesta no conserva tu nivel de apoyo. No se guardó ningún cambio")
    numbers = set(re.findall(r"\d+(?:[.,]\d+)?", text))
    if not numbers <= set(re.findall(r"\d+(?:[.,]\d+)?", source)) or "%" in text and "%" not in source:
        raise ValueError("La propuesta añadió una cifra sin respaldo. No se guardó ningún cambio")
    if not set(re.findall(r"(?<!\w)[-−]\d+(?:[.,]\d+)?", original)) <= set(re.findall(r"(?<!\w)[-−]\d+(?:[.,]\d+)?", text)):
        raise ValueError("La propuesta cambió el signo de una cifra. No se guardó ningún cambio")
    tools = {"excel", "sql", "python", "sap", "salesforce", "aws", "azure", "power bi", "react", "docker", "java", "jira", "tableau"}
    tools.update(fold(value) for value in re.findall(r"\b[A-Z]{2,}[A-Za-z0-9.+#-]*\b", text))
    for tool in tools:
        if re.search(r"(?<!\w)" + re.escape(tool) + r"(?!\w)", fold(text)) and not re.search(r"(?<!\w)" + re.escape(tool) + r"(?!\w)", source):
            raise ValueError("La propuesta añadió una herramienta sin respaldo. No se guardó ningún cambio")
    return {"text": text, "method": "local-ai", "changes": ["Propuesta redactada con IA local a partir de tu descripción. Revisa que cada frase refleje tu experiencia."],
            "questions": [generated["idea"].strip()[:300]] if generated.get("idea", "").strip() else []}


def responsibility_parts(description):
    """Recover responsibilities concatenated by PDF extraction, without truncation."""
    source = re.sub(r"(?<=[a-záéíóúñ0-9])\s+(?=(?:Gestión|Análisis|Elaboración|Validación|Preparación|Atención|Apoyo|Participación|Diseño|Ejecución|Identificación|Trabajo|Desarrollo|Actualización|Control|Seguimiento)\b)", "\n", description)
    parts = [re.sub(r"^(?:[•*]|-(?=\s))\s*", "", part.strip()).rstrip(".") for part in re.split(r"\n+|;\s*|(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])", source)]
    return [part for part in parts if part]


def validate_complete_rewrite(generated, record, result):
    facts = responsibility_parts(str(record.get("description") or ""))
    actions = generated.get("actions")
    if not isinstance(actions, list) or not facts:
        raise ValueError("No se obtuvo una propuesta completa. Tu texto se conserva")
    indexed = {}
    for item in actions:
        if not isinstance(item, dict) or type(item.get("index")) is not int or not isinstance(item.get("text"), str) or item["index"] in indexed:
            raise ValueError("No se obtuvo una propuesta completa. Tu texto se conserva")
        indexed[item["index"]] = item["text"]
    rewritten, retained = [], 0
    # Check each source responsibility independently. An unsafe embellishment must
    # never delete another duty, nor silently turn a complete CV into a summary.
    stop = set("para mediante desde hasta sobre como entre estas estos otras otros tareas trabajo responsable responsabilidades realizacion elaboracion gestion analisis validacion desarrollo apoyo participacion seguimiento informacion herramientas tecnologicas".split())
    for index, fact in enumerate(facts):
        candidate = indexed.get(index, "")
        try:
            # Correct recurring first-person spelling slips of the compact local
            # model, only at the start of a past-tense action (not inside quotes).
            current = record.get("is_current") is True or fold(record.get("end_year")) in {"presente", "actualidad", "actual"}
            if not current:
                candidate = re.sub(r"^(?:Analize|Análize|Análice|Analice)\b", "Analicé", candidate)
                for wrong, correct in (("Gestione", "Gestioné"), ("Controle", "Controlé"), ("Valide", "Validé"), ("Elabore", "Elaboré"), ("Apoye", "Apoyé"), ("Realice", "Realicé")):
                    candidate = re.sub(r"^" + wrong + r"\b", correct, candidate)
            checked = validate_generated_text({"text": candidate}, {**record, "description": fact})["text"]
            anchors = {word[:5] for word in re.findall(r"\b[a-z]{5,}\b", fold(fact)) if word not in stop}
            target = fold(checked)
            coverage = sum(anchor in target for anchor in anchors) / max(1, len(anchors))
            if anchors and coverage < .65 or len(checked) < len(fact) * .65:
                raise ValueError("Incomplete responsibility")
            rewritten.append(checked.strip("•- ").rstrip("."))
        except ValueError:
            rewritten.append(fact)
            retained += 1
    if result.strip():
        rewritten.append(result.strip().rstrip("."))
    text = "\n".join("• " + line + "." for line in rewritten) if generated.get("style") == "bullets" else " ".join(line + "." for line in rewritten)
    if len(text) > 3000:
        raise ValueError("La propuesta supera el espacio disponible. Acorta la descripción o el resultado adicional")
    changes = [f"Revisamos las {len(facts)} responsabilidades de tu descripción, sin eliminar ninguna."]
    if retained:
        changes.append(f"Conservamos {retained} en su forma original porque la propuesta no mantenía suficiente información o añadía hechos sin respaldo.")
    idea = str(generated.get("idea") or "").strip()[:300]
    if re.search(r"\bcomo\b.*\b(?:puedo|podria|mejorar|optimizar)\b", fold(idea)):
        idea = "¿Qué entrega concreta realizaste y qué parte estuvo a tu cargo?"
    return {"text": text, "method": "local-ai", "changes": changes, "questions": [idea] if idea else []}

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
