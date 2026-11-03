# ruff: noqa: F811
from copy import deepcopy
from datetime import datetime

from test_api_flows import client, company_account, register  # noqa: F401
from test_ecosystem import administrator
from test_learning_resources import content

from app.infrastructure.database.models import LearningPlan, LearningResource


def authored():
    return {"mode": "custom", "rationale": "El caso refuerza las operaciones y conceptos del temario revisado.", "draft": {
        "title": "Revisa entregas de inventario", "scenario": "Se reciben diez pedidos ficticios y dos se devuelven. Organiza la revisión y calcula cuántos quedan.",
        "steps": ["Recibir los pedidos", "Comprobar los datos", "Registrar las diferencias"],
        "calculation_prompt": "De diez pedidos se devuelven dos. ¿Cuántos pedidos quedan?", "calculation_answer": 8,
        "calculation_feedback": "Se restan las dos devoluciones a los diez pedidos: 10 - 2 = 8.",
        "terms": ["Pedido", "Devolución", "Registro"], "meanings": ["Solicitud de entrega", "Retorno del pedido", "Anotación de un hecho"]}}


def create(client, admin, **changes):
    response = client.post("/api/v1/admin/learning/resources", headers=admin, json=content(**changes))
    assert response.status_code == 201, response.text
    return next(row for row in response.json() if row["title"] == changes.get("title", "Curso de Python"))


def test_course_without_reviewed_practice_has_independent_progress_and_certificate(client):
    admin = administrator(client)
    source = create(client, admin, title="Curso de Python sin actividades vinculadas")
    user, candidate = register(client, "course-independent")
    _, other = register(client, "course-independent-other")
    base = f"/api/v1/learning/plans/{source['id']}"
    plan = client.put(base, headers=candidate, json={}).json()[0]
    assert plan["resource"]["journey"] is None
    assert client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "finish": True}).status_code == 409
    certificate = {"name": "Certificado que expidió el proveedor", "credential_url": "https://example.com/credential", "year": datetime.utcnow().year, "has_certificate": True}
    assert client.post(base + "/certificate", headers=candidate, json=certificate).status_code == 409
    assert client.patch(base + "/course", headers=other, json={"version": plan["version"], "completed": True}).status_code == 404
    done = client.patch(base + "/course", headers=candidate, json={"version": plan["version"], "completed": True})
    assert done.status_code == 200, done.text
    assert done.json()[0]["progress"]["course_completed"] is True
    assert client.post(base + "/certificate", headers=candidate, json=certificate).status_code == 200
    assert client.patch(base + "/course", headers=candidate, json={"version": plan["version"], "completed": False}).status_code == 409
    passport = client.get("/api/v1/learning/passport", headers=candidate).json()
    assert passport["learning_results"] == [] and len(passport["course_results"]) == 1
    assert len(passport["certificates"]) == 1 and passport["assessments"] == []
    assert client.get("/api/v1/profiles/me", headers=candidate).json()["skills"] == []
    with client.session_factory() as db:
        assert db.query(LearningPlan).filter_by(user_id=user["id"]).one().progress["practice_spec"] is None


def test_completed_course_claims_only_selected_skills_without_a_certificate(client):
    source = create(client, administrator(client), skills=["Python", "SQL"], details={"certificate_cost": "none"})
    _, candidate = register(client, "completed-skills", skills=["excel"])
    _, other = register(client, "completed-skills-other")
    base = f"/api/v1/learning/plans/{source['id']}"
    plan = client.put(base, headers=candidate, json={}).json()[0]
    claim = {"skills": ["Python"], "confirm": True}
    assert client.post(base + "/skills", headers=other, json=claim).status_code == 404
    assert client.post(base + "/skills", headers=candidate, json=claim).status_code == 409
    done = client.patch(base + "/course", headers=candidate, json={"version": plan["version"], "completed": True}).json()[0]
    assert client.post(base + "/skills", headers=candidate).status_code == 422
    assert client.post(base + "/skills", headers=candidate, json={"skills": ["Python"], "confirm": False}).status_code == 422
    assert client.post(base + "/skills", headers=candidate, json={"skills": ["inventada"], "confirm": True}).status_code == 422
    assert client.post(base + "/skills", headers=candidate, json={"skills": [], "confirm": True}).status_code == 422
    response = client.post(base + "/skills", headers=candidate, json=claim)
    assert response.status_code == 200, response.text
    assert response.json()[0]["remaining_skills"] == ["sql"]
    assert response.json()[0]["skills_added"] is False
    assert client.post(base + "/skills", headers=candidate, json=claim).status_code == 200
    profile = client.get("/api/v1/profiles/me", headers=candidate).json()
    assert set(profile["skills"]) == {"excel", "python"}
    passport = client.get("/api/v1/learning/passport", headers=candidate).json()
    assert passport["certificates"] == [] and passport["assessments"] == []
    assert len(passport["course_results"]) == 1 and passport["learning_results"] == []
    assert client.patch(base + "/course", headers=candidate, json={"version": done["version"], "completed": False}).status_code == 200
    assert client.post(base + "/skills", headers=candidate, json={"skills": ["SQL"], "confirm": True}).status_code == 409
    assert set(client.get("/api/v1/profiles/me", headers=candidate).json()["skills"]) == {"excel", "python"}


def test_training_without_advertised_certificate_is_idempotent_and_can_gain_a_certificate(client):
    source = create(client, administrator(client), details={"certificate_cost": "none"})
    _, candidate = register(client, "training-evidence")
    base = f"/api/v1/learning/plans/{source['id']}"
    plan = client.put(base, headers=candidate, json={}).json()[0]
    assert client.post(base + "/evidence", headers=candidate).status_code == 409
    done = client.patch(base + "/course", headers=candidate, json={"version": plan["version"], "completed": True})
    assert done.status_code == 200
    for _ in range(2):
        response = client.post(base + "/evidence", headers=candidate)
        assert response.status_code == 200, response.text
    profile = client.get("/api/v1/profiles/me", headers=candidate).json()
    evidence = client.get("/api/v1/matching/evidence", headers=candidate).json()
    assert len(evidence) == 1
    assert evidence[0]["kind"] == "training"
    assert profile["certifications"] == []
    certificate = {"name": "Certificado del proveedor", "credential_url": "https://example.com/credential", "year": datetime.utcnow().year, "has_certificate": True}
    for _ in range(2):
        response = client.post(base + "/certificate", headers=candidate, json=certificate)
        assert response.status_code == 200, response.text
    profile = client.get("/api/v1/profiles/me", headers=candidate).json()
    evidence = client.get("/api/v1/matching/evidence", headers=candidate).json()
    assert len(evidence) == len(profile["certifications"]) == 1
    assert evidence[0]["kind"] == "certificate"


def test_authored_practice_solutions_are_private_and_course_progress_survives_submissions(client):
    admin = administrator(client)
    source = create(client, admin, practice=authored())
    user, candidate = register(client, "course-authored")
    _, company = company_account(client, "course-authoring-forbidden")
    assert client.get("/api/v1/admin/learning/practice-templates", headers=candidate).status_code == 403
    assert client.get("/api/v1/admin/learning/practice-templates/python", headers=company).status_code == 403
    assert "answer" in client.get("/api/v1/admin/learning/practice-templates/python", headers=admin).json()["activities"][0]
    catalog = client.get("/api/v1/learning/catalog", params={"area": "all"}, headers=candidate).json()
    public = next(row for row in catalog["resources"] if row["id"] == source["id"])
    assert "draft" not in public["practice"]
    assert public["journey"] is None  # Course catalog no longer offers per-course practices.
    base = f"/api/v1/learning/plans/{source['id']}"
    plan = client.put(base, headers=candidate, json={}).json()[0]
    with client.session_factory() as db:
        snapshot = deepcopy(db.query(LearningPlan).filter_by(user_id=user["id"]).one().progress["practice_spec"])
        resource = db.get(LearningResource, source["id"])
        updated = authored(); updated["draft"]["calculation_answer"] = 99
        resource.content = {**resource.content, "practice": updated}
        db.commit()
    answers = {item["id"]: item["answer"] for item in snapshot["activities"]}
    submitted = client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "activity_answers": answers, "finish": True})
    assert submitted.status_code == 200, submitted.text
    plan = submitted.json()[0]
    assert plan["status"] == "in_progress" and not plan["progress"]["course_completed"]
    assert plan["progress"]["score"] == 100 and len(plan["progress"]["activity_feedback"]) == 3
    assert "draft" not in plan["resource"]["practice"] and "practice_spec" not in plan["progress"]
    result = client.get("/api/v1/learning/passport", headers=candidate).json()
    assert result["learning_results"][0]["title"] == authored()["draft"]["title"] and result["course_results"] == []
    plan = client.patch(base + "/course", headers=candidate, json={"version": plan["version"], "completed": True}).json()[0]
    retry = client.patch(base + "/journey", headers=candidate, json={"version": plan["version"], "retry": True})
    assert retry.status_code == 200 and retry.json()[0]["progress"]["course_completed"]


def test_practice_binding_requires_reviewed_mapping_and_valid_solutions(client):
    admin = administrator(client)
    for practice in [{"mode": "template", "template_id": "not-available", "rationale": "Este caso se revisó contra el contenido del curso."}, {"mode": "custom", "rationale": "Se revisó el temario completo."}, {**authored(), "draft": {**authored()["draft"], "meanings": ["Solo dos", "Definiciones"]}}]:
        assert client.post("/api/v1/admin/learning/resources", headers=admin, json=content(practice=practice)).status_code == 422
