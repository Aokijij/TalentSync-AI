from app.domain.services.application_preparation import (
    interview_questions,
    preparation_revision,
)


def test_questions_use_actual_responsibilities_and_prioritize_essential_requirements():
    profile = {"skills": ["sql"], "experiences": [{"role": "Analista", "company": "Equipo", "description": "Preparé consultas SQL para reportes."}]}
    job = {"title": "Analista de inventarios", "description": "Reconciliar existencias y entregas del almacén. Coordinar diferencias con el equipo de distribución.",
           "requirements": "Consultas SQL para detectar registros duplicados y movimientos sin soporte.",
           "skills": ["excel", "git", "python", "html", "sql"],
           "skill_requirements": [{"skill": "sql", "essential": True, "weight": 5, "level": "advanced"}]}
    questions = interview_questions(profile, job)
    skill_questions = [row for row in questions if row.get("skill")]
    assert skill_questions[0]["skill"] == "sql"
    assert skill_questions[0]["required_level"] == "avanzado"
    assert skill_questions[0]["category"] == "Habilidad esencial"
    assert "duplicados" in skill_questions[0]["context"]
    assert "duplica filas" in skill_questions[0]["follow_ups"][0]
    assert skill_questions[0]["experiences"][0]["role"] == "Analista"
    assert questions[0]["context"] == "Reconciliar existencias y entregas del almacén."
    assert "distribución" in questions[-1]["context"]
    assert all(len(row["context"]) <= 320 for row in questions)


def test_requirement_only_aliases_are_deduplicated_and_absent_skills_do_not_imply_experience():
    job = {"title": "Desarrollo de servicios", "skills": ["js", "JavaScript"],
           "skill_requirements": [{"skill": "python", "essential": True}],
           "description": "<p>Construir integraciones con servicios de pedidos.</p>", "requirements": ""}
    questions = interview_questions({"skills": [], "experiences": []}, job)
    rows = [row for row in questions if row.get("skill")]
    assert len(rows) == 2
    assert all(not row["in_profile"] and not row["experiences"] for row in rows)
    assert all("<p>" not in row["context"] for row in questions)
    assert "pruebas" in rows[0]["follow_ups"][0]
    assert len({row["id"] for row in questions}) == len(questions)


def test_question_ids_keep_saved_answers_addressable_and_private_details_do_not_change_revision():
    job = {"title": "Analista", "skills": ["sql"], "description": "Preparar reportes del inventario."}
    before = interview_questions({}, job)
    after = interview_questions({}, {**job, "description": "Preparar reportes del inventario y las entregas."})
    assert [row["id"] for row in before] == [row["id"] for row in after]
    assert preparation_revision({}, job) != preparation_revision({}, {**job, "description": "Otra responsabilidad"})
    assert preparation_revision({"birth_date": "1999-01-01", "identification_number": "private"}, job) == preparation_revision({}, job)


def test_essential_prioritization_keeps_an_answered_legacy_skill_in_the_practice():
    old_offer = {"title": "Desarrollo", "skills": ["python", "sql", "git", "excel", "react"]}
    old = interview_questions({}, old_offer)
    answered_id = next(row["id"] for row in old if row.get("skill") == "excel")
    prioritized = {**old_offer, "skill_requirements": [{"skill": "react", "essential": True, "weight": 5}]}
    new = interview_questions({}, prioritized, saved_question_ids={answered_id})
    assert next(row for row in new if row.get("skill"))["skill"] == "react"
    assert answered_id in {row["id"] for row in new}
