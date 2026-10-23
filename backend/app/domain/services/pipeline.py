def stages_for(job):
    """Legacy vacancies without a configured pipeline use the standard stages."""
    return job.pipeline_stages or default_stages()


def stage_id_for(application):
    status = str(application.status)
    if status in {"accepted", "hired"}:
        return "hired"
    if status == "rejected":
        return "rejected"
    return application.pipeline_stage or {
        "submitted": stages_for(application.job)[0]["id"], "seen": stages_for(application.job)[0]["id"],
        "shortlisted": "reviewing", "technical_interview": "interview", "psychometric_test": "interview",
    }.get(status, status)


def default_stages():
    return [
        {"id": "submitted", "title": "Recibidas"},
        {"id": "reviewing", "title": "En revisión"},
        {"id": "interview", "title": "Entrevista"},
        {"id": "hired", "title": "Contratados"},
        {"id": "rejected", "title": "No seleccionados"},
    ]
