"""Explicit test data, independent of the editorial learning catalogue."""
from app.infrastructure.database.models import LearningPlan, LearningResource


def publish_course(client, resource_id, *, category="technology", skills=None):
    with client.session_factory() as db:
        db.add(LearningResource(id=resource_id, active=True, content={
            "title": "Curso de revisión", "provider": "Proveedor de pruebas",
            "url": f"https://education.example.test/{resource_id}",
            "instructions": "Revisa los contenidos y practica las habilidades del curso.",
            "category": category, "kind": "course", "hours": 2,
            "skills": skills or ["python"], "cost": "free",
            "sponsored": False, "affiliate": False,
        }))
        db.commit()


def retain_legacy_plan(client, user_id, resource_id):
    """Emulate a saved plan from before retirement, without reopening enrolment."""
    with client.session_factory() as db:
        db.add(LearningPlan(user_id=user_id, resource_id=resource_id,
                            status="in_progress", progress={}))
        db.commit()
