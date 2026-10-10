from app.domain.services.offer_review import review_offer


def discovery_signals(job, match_percentage):
    internal = getattr(job, "source_kind", "internal") == "internal"
    score = review_offer(job)["score"] if internal else None
    bonus = round((score - 50) / 10, 2) if score is not None else 0
    return {"policy": "affinity-bands-quality-v1", "quality_score": score, "quality_bonus": bonus,
            "affinity_band": min(9, int(match_percentage // 10)),
            "notice": "La calidad ayuda a ordenar ofertas dentro de bandas de diez puntos de compatibilidad. Su efecto es de hasta cinco puntos de ordenación; no cambia tu porcentaje. Las ofertas externas tienen un efecto neutro."}


def discovery_key(row):
    signals = row.discovery
    personal = row.personalization
    return (signals["visibility_reduced"], -signals["affinity_band"],
            -int(personal.get("interested") is True),
            -(personal.get("score") if personal.get("score") is not None else 50),
            -(row.match_percentage + signals["quality_bonus"]), -row.match_percentage, row.job_id)
