from app.domain.services.offer_review import review_offer


def discovery_signals(job, match_percentage):
    internal = getattr(job, "source_kind", "internal") == "internal"
    score = review_offer(job)["score"] if internal else None
    bonus = round((score - 50) * .25, 2) if score is not None else 0
    return {"policy": "affinity-clarity-v2", "quality_score": score, "quality_bonus": bonus,
            "affinity_band": min(9, int(match_percentage // 10)),
            "notice": "Recomendadas pondera 80% compatibilidad y 20% claridad, con una señal adicional de interés. Una oferta clara puede adelantar a otra con compatibilidad cercana. La confianza de la empresa sigue siendo prioritaria. Tu porcentaje no cambia; las ofertas externas tienen claridad neutral."}


def discovery_key(row):
    signals = row.discovery
    personal = row.personalization
    interest = (4 if personal.get("interested") is True else 0) + ((personal.get("score") if personal.get("score") is not None else 50) - 50) * .02
    return (signals["visibility_reduced"], -(row.match_percentage + signals["quality_bonus"] + interest), -row.match_percentage, row.job_id)
