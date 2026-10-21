"""Types describe the training record, not an authenticity assessment."""
import re

from app.domain.services.professions import normalize

TRAINING_TYPES = {
    "course": "Curso", "certificate": "Certificado", "diploma": "Diplomado",
    "workshop": "Taller", "seminar": "Seminario", "other": "Otra formación",
}


def infer_training_type(value):
    text = normalize(value)
    for kind, pattern in [("diploma", r"\bdiplomad[oa]\b"), ("course", r"\bcurso\b"), ("workshop", r"\btaller\b"), ("seminar", r"\bseminario\b"), ("certificate", r"\bcertific(?:acion|ado|ada)\b")]:
        if re.search(pattern, text):
            return kind
    return None


def validate_training(items):
    for item in items or []:
        if item.get("kind") not in {None, "", *TRAINING_TYPES}:
            raise ValueError("Selecciona un tipo válido: curso, certificado, diplomado, taller, seminario u otra formación")
    return items
