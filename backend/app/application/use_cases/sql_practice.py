from collections import Counter
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.learning import grant_fundamentals, public_attempt
from app.domain.services.sql_challenges import CHALLENGES, TABLES


def view(row):
    result = {key: getattr(row, key) for key in ("id", "assessment_id", "skill", "status", "started_at", "expires_at", "score", "passed", "feedback")}
    bank = CHALLENGES[row.assessment_id]
    result.update(title=bank["title"], prompt=bank["prompt"], columns=bank["columns"], tables=TABLES,
                  sample=row.snapshot[0]["dataset"], notice="Consulta SQLite de solo lectura sobre datos ficticios. Debes superar los tres conjuntos de comprobación. Acredita únicamente consultas SQL básicas durante 180 días.")
    return result


def start(db, user, challenge_id):
    bank = CHALLENGES.get(challenge_id)
    if bank is None:
        raise UseCaseError(status_code=404, detail="Reto no disponible")
    now = datetime.utcnow()
    attempts = [row for row in db.learning.attempts(user.id) if row.assessment_id == challenge_id]
    if attempts and attempts[0].status == "active" and attempts[0].expires_at > now:
        return view(attempts[0])
    if attempts and attempts[0].started_at > now - timedelta(days=1):
        raise UseCaseError(status_code=429, detail="Puedes iniciar otro intento después de 24 horas")
    row = db.learning.new_attempt(id=uuid5(NAMESPACE_URL, f"sql-practice:{user.id}:{challenge_id}:{now.date().isoformat()}").hex,
        user_id=user.id, assessment_id=challenge_id, skill=bank["skill"], version=bank["version"], started_at=now,
        expires_at=now + timedelta(minutes=bank["minutes"]), status="active", feedback=[],
        snapshot=[{"dataset": data, "expected": expected, "columns": bank["columns"]} for data, expected in zip(bank["datasets"], bank["expected"], strict=True)])
    db.add(row)
    record_event(db, "assessment.started", "profile", user.profile.id, actor_user_id=user.id, details={"assessment_id": challenge_id})
    db.commit()
    return view(row)


def _attempt(db, user, attempt_id):
    row = db.learning.attempt(attempt_id)
    if row is None or row.user_id != user.id or row.assessment_id not in CHALLENGES:
        raise UseCaseError(status_code=404, detail="Reto no encontrado")
    if row.status != "active" or row.expires_at <= datetime.utcnow():
        raise UseCaseError(status_code=409, detail="El intento venció o ya se entregó")
    return row


def preview(db, user, attempt_id, query, sandbox):
    row = _attempt(db, user, attempt_id)
    return sandbox.run(query, row.snapshot[0]["dataset"])


def submit(db, user, attempt_id, query, sandbox):
    row = _attempt(db, user, attempt_id)
    now = datetime.utcnow()
    if not db.learning.claim_submission(row.id, user.id, now):
        raise UseCaseError(status_code=409, detail="El intento venció o ya se entregó")
    outcomes = []
    for test in row.snapshot:
        actual = sandbox.run(query, test["dataset"])
        passed = bool(actual["ok"] and actual["columns"] == test["columns"]
                      and Counter(tuple(item) for item in actual["rows"]) == Counter(tuple(item) for item in test["expected"]))
        outcomes.append(passed)
    row.score = round(sum(outcomes) / len(outcomes) * 100, 2)
    row.passed = all(outcomes)
    row.feedback = [{"question_id": f"dataset-{index + 1}", "correct": passed,
                     "message": "Comprobación superada" if passed else "Revisa columnas, agrupación, estados de pedidos y clientes sin coincidencias."} for index, passed in enumerate(outcomes)]
    row.valid_until = now + timedelta(days=180) if row.passed else None
    if row.passed:
        grant_fundamentals(db, user, row, now)
    record_event(db, "assessment.completed", "profile", user.profile.id, actor_user_id=user.id,
                 details={"assessment_id": row.assessment_id, "result": "passed" if row.passed else "not_passed", "version": row.version})
    db.commit()
    return public_attempt(row)
