def stages_for(job):
    """Legacy vacancies without a configured pipeline use the standard stages."""
    return job.pipeline_stages or default_stages()


def default_stages():
    return [
        {"id": "submitted", "title": "Recibidas"},
        {"id": "reviewing", "title": "En revisión"},
        {"id": "interview", "title": "Entrevista"},
        {"id": "hired", "title": "Contratados"},
        {"id": "rejected", "title": "No seleccionados"},
    ]
