"""Score bands describe information completeness, independently of publication gates."""
RATING_SCALE = [
    {"code": "A", "label": "Excelente", "minimum": 90, "maximum": 100, "description": "Información muy completa y clara. Revisa también los requisitos de publicación y cualquier contradicción."},
    {"code": "B", "label": "Buena", "minimum": 75, "maximum": 89, "description": "La oferta tiene una base sólida; completa los aspectos señalados para que sea más útil al candidato."},
    {"code": "C", "label": "Por mejorar", "minimum": 50, "maximum": 74, "description": "Faltan datos relevantes de condiciones, funciones, requisitos o proceso. Prioriza las mejoras obligatorias."},
    {"code": "D", "label": "Inicial", "minimum": 0, "maximum": 49, "description": "La oferta necesita más información para que una persona pueda decidir si se postula."},
]


def offer_rating(score):
    return next(dict(row) for row in RATING_SCALE if score >= row["minimum"])
