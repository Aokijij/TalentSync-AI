from app.domain.services.skills import skill_set


def consented(user):
    return user.role == "candidate" and (user.privacy_preferences or {}).get("personalize_recommendations", False)


def synthetic_email(email):
    domain = email.casefold().split("@")[-1]
    return domain.endswith(".test") or any(domain == value or domain.endswith("." + value) for value in ["example.com", "example.net", "example.org"])


def collaborative_interest(profile, job_id, signals):
    own = skill_set(profile.skills)
    neighbors = []
    used = set()
    for row in signals:
        if row.user_id == profile.user_id or row.job_id != job_id or row.user_id in used or not consented(row.user) or row.user.profile is None:
            continue
        skills = skill_set(row.user.profile.skills)
        similarity = len(own & skills) / max(1, len(own | skills))
        if similarity >= .2:
            neighbors.append((similarity, row.interested))
            used.add(row.user_id)
    neighbors = sorted(neighbors, reverse=True)[:50]
    if len(neighbors) < 3:
        return {"score": None, "sample_sufficient": False}
    return {"score": round(100 * sum(weight * label for weight, label in neighbors) / sum(weight for weight, _ in neighbors), 1), "sample_sufficient": True}


def training_gate(rows):
    positives = sum(row["label"] for row in rows)
    return {"rows": len(rows), "users": len({row["user_id"] for row in rows}), "jobs": len({row["job_id"] for row in rows}),
            "positives": positives, "negatives": len(rows) - positives,
            "ready": len(rows) >= 100 and len({row["user_id"] for row in rows}) >= 20 and len({row["job_id"] for row in rows}) >= 10 and min(positives, len(rows) - positives) >= 20}
