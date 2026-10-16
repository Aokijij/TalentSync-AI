from types import SimpleNamespace

from app.application.errors import UseCaseError
from app.application.use_cases.career_coach import owner_profile
from app.domain.services.career_coach import fingerprint
from app.domain.services.professional_summary import (
    fact_text,
    summary_facts,
    validate_summary,
)


def generate(user, payload, *, writer, nlp):
    profile = owner_profile(user)
    draft = payload.get("profile")
    facts = summary_facts(SimpleNamespace(**draft) if draft is not None else profile)
    has_context = any((facts["habilidades"], facts["formacion_anterior"], facts["resumen_actual"],
        any(row["funciones"] or row["cargo"] for row in facts["experiencias"]), any(row["titulo"] for row in facts["formacion"])))
    if len(fact_text(facts).strip()) < 20 or not has_context:
        raise UseCaseError(status_code=422, detail="Completa tu profesión y alguna experiencia, formación o habilidad para preparar un resumen con tus datos")
    if writer is None:
        raise UseCaseError(status_code=503, detail="El generador local aún no está preparado. Puedes escribir y guardar tu propio resumen")
    try:
        generated = writer.generate_summary(facts, tone=payload["tone"])
        text = validate_summary(generated, facts, extract_skills=nlp.extract_skills)
    except ValueError as error:
        raise UseCaseError(status_code=422, detail=str(error)) from None
    return {"text": text, "method": "local-ai", "source_version": fingerprint(facts)}
