import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.errors import UseCaseError
from app.core.config import Settings
from app.domain.services.career_writing import validate_generated_text
from app.infrastructure.database.models import AIWriterUsage
from app.infrastructure.nlp.groq_writer import (
    GroqCareerWriter,
    Redactions,
    writer_status,
)
from app.infrastructure.nlp.writing_budget import WritingBudget


def config(**values):
    return Settings(_env_file=None, secret_key="synthetic-secret-for-tests-only-2026", career_writer_provider="groq",
                    groq_api_key=SecretStr("synthetic-provider-key"), groq_free_plan_confirmed=True,
                    groq_zero_data_retention_confirmed=True).model_copy(update=values)


@pytest.fixture
def ledger(tmp_path):
    engine = create_engine("sqlite:///" + str(tmp_path / "usage.db"), connect_args={"check_same_thread": False})
    AIWriterUsage.__table__.create(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


def completion(actions, **extra):
    return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"actions": actions, "idea": "¿Qué registros actualizaste?"})}}],
            "usage": {"total_tokens": 600}, **extra}


def test_minimized_structured_request_restores_values_without_sending_identity(ledger):
    calls = []
    def serve(request):
        assert request.url == "https://api.groq.com/openai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer synthetic-provider-key"
        data = json.loads(request.content)
        calls.append(data)
        assert data["model"] == "openai/gpt-oss-20b" and data["service_tier"] == "on_demand"
        assert data["response_format"]["json_schema"]["strict"] is True
        assert "store" not in data and "tools" not in data
        facts = json.loads(data["messages"][1]["content"].removeprefix("DATOS: "))
        assert facts["actual"] is True and facts["tareas"][0]["index"] == 0
        assert not any(value in request.content.decode() for value in ["Marta", "Compañía Privada", "example.test", "3001234567", "99", "_owner_id"])
        return httpx.Response(200, json=completion(facts["tareas"]))
    cfg = config()
    writer = GroqCareerWriter(cfg, budget=WritingBudget(cfg, ledger), transport=httpx.MockTransport(serve))
    record = {"role": "Analista", "company": "Compañía Privada", "is_current": True,
              "description": "Apoyo a Marta en Compañía Privada. Contacto marta@example.test, 3001234567",
              "_owner_id": 99, "_private_terms": ["Marta", "Compañía Privada"]}
    result = writer.generate(record, style="paragraph", result="")
    assert "Marta" in result["actions"][0]["text"] and "Compañía Privada" in result["actions"][0]["text"]
    assert "marta@example.test, 3001234567" in result["actions"][1]["text"]
    assert len(calls) == 1
    with ledger() as db:
        rows = db.query(AIWriterUsage).all()
        assert len(rows) == 2 and all(row.requests == 1 and row.tokens == 600 for row in rows)
        assert set(AIWriterUsage.__table__.columns.keys()) == {"id", "requests", "tokens", "minute", "minute_requests", "minute_tokens", "version"}


def test_redaction_preserves_json_types_keys_and_quotes():
    redact = Redactions(["index", 'Persona "Ejemplo"'])
    source = {"index": 3, "actual": False, "text": 'Persona "Ejemplo" en https://example.test/cv con CC 12345678'}
    hidden = redact.hide(source)
    assert hidden["index"] == 3 and hidden["actual"] is False
    assert "example.test" not in json.dumps(hidden) and "12345678" not in json.dumps(hidden)
    assert redact.restore(json.loads(json.dumps(hidden))) == source


@pytest.mark.parametrize("response,code", [
    (httpx.Response(429, text="private provider body"), 429),
    (httpx.Response(401, text="private provider body"), 503),
    (httpx.Response(307, headers={"location": "https://unexpected.test"}), 503),
    (httpx.Response(200, json={}), 503),
    (httpx.Response(200, json=completion([], choices=[{"finish_reason": "length", "message": {"content": "{}"}}])), 503),
    (httpx.Response(200, text="not json private provider body"), 503),
    (httpx.Response(200, content=b"x" * 100001), 503),
])
def test_failures_are_safe_never_redirect_or_retry_and_still_count(ledger, response, code):
    calls = []
    def serve(request):
        calls.append(request.url)
        return response
    cfg = config()
    writer = GroqCareerWriter(cfg, budget=WritingBudget(cfg, ledger), transport=httpx.MockTransport(serve))
    with pytest.raises(UseCaseError) as error:
        writer.generate({"description": "Actualización de registros"}, style="paragraph", result="")
    assert error.value.status_code == code and "private provider body" not in error.value.detail
    assert len(calls) == 1
    with ledger() as db:
        assert db.query(AIWriterUsage).one().requests == 1


def test_timeout_preserves_text_and_has_no_automatic_second_call(ledger):
    calls = []
    def serve(request):
        calls.append(1)
        raise httpx.ReadTimeout("private input", request=request)
    cfg = config()
    writer = GroqCareerWriter(cfg, budget=WritingBudget(cfg, ledger), transport=httpx.MockTransport(serve))
    with pytest.raises(UseCaseError) as error:
        writer.generate({"description": "Actualización de registros"}, style="paragraph", result="")
    assert error.value.status_code == 504 and "private input" not in error.value.detail and len(calls) == 1


@pytest.mark.parametrize("missing", ["groq_api_key", "groq_free_plan_confirmed", "groq_zero_data_retention_confirmed"])
def test_external_writer_cannot_be_enabled_without_all_setup_conditions(missing):
    cfg = config(**{missing: None if missing == "groq_api_key" else False})
    assert not writer_status(cfg)["available"]
    with pytest.raises(UseCaseError):
        GroqCareerWriter(cfg)
    assert "synthetic-provider-key" not in str(cfg)


def test_provider_payload_is_subject_to_existing_per_responsibility_grounding(ledger):
    cfg = config()
    writer = GroqCareerWriter(cfg, budget=WritingBudget(cfg, ledger), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=completion([
        {"index": 0, "text": "Lideré 50 personas y aumenté las ventas un 90%."},
        {"index": 1, "text": "Desarrollé infraestructura Kubernetes."},
    ]))))
    record = {"description": "Atención a clientes y seguimiento de pedidos\nApoyo en actualización de registros"}
    text = validate_generated_text(writer.generate(record, style="bullets", result=""), record)["text"]
    assert "50" not in text and "90" not in text and "Kubernetes" not in text
    assert "clientes" in text and "pedidos" in text and "Apoyo" in text and "registros" in text


def test_usage_persists_across_instances_and_refunds_only_actual_tokens(ledger):
    cfg = config(groq_user_daily_requests=1)
    now = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)
    first = WritingBudget(cfg, ledger, lambda: now)
    ticket = first.reserve(2000, 7)
    first.settle(ticket, 500)
    other = WritingBudget(cfg, ledger, lambda: now + timedelta(minutes=2))
    with pytest.raises(UseCaseError) as error:
        other.reserve(2000, 7)
    assert error.value.status_code == 429
    # Another candidate can use the shared balance; a new UTC day resets usage.
    other.reserve(2000, 8)
    WritingBudget(cfg, ledger, lambda: now + timedelta(days=1)).reserve(2000, 7)
    with ledger() as db:
        row = db.get(AIWriterUsage, "groq-20261103")
        assert row.requests == 2 and row.tokens == 2500


def test_previous_minute_refund_cannot_reduce_new_minute_reservation(ledger):
    cfg = config()
    now = [datetime(2026, 11, 3, 12, tzinfo=timezone.utc)]
    budget = WritingBudget(cfg, ledger, lambda: now[0])
    ticket = budget.reserve(2000)
    now[0] += timedelta(minutes=1)
    budget.reserve(3000)
    budget.settle(ticket, 500)
    with ledger() as db:
        row = db.query(AIWriterUsage).one()
        assert row.tokens == 3500 and row.minute_tokens == 3000 and row.minute_requests == 1


def test_shared_budget_does_not_oversubscribe_concurrent_workers(ledger):
    cfg = config(groq_daily_requests=3)
    def attempt(_):
        try:
            WritingBudget(cfg, ledger).reserve(100)
            return True
        except UseCaseError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(12)))
    with ledger() as db:
        row = db.query(AIWriterUsage).one()
        assert sum(results) == 3 and row.requests == 3 and row.tokens == 300


def test_minute_token_and_request_caps_prevent_a_provider_call(ledger):
    cfg = config(groq_minute_requests=1)
    budget = WritingBudget(cfg, ledger)
    with pytest.raises(UseCaseError) as error:
        budget.reserve(8000)
    assert error.value.status_code == 422
    budget.reserve(100)
    with pytest.raises(UseCaseError) as error:
        budget.reserve(100)
    assert error.value.status_code == 429


def test_local_structured_summary_remains_available_without_a_model():
    status = writer_status(SimpleNamespace(career_writer_provider="local", career_writer_model="", career_writer_executable=""))
    assert status["summary_available"] and not status["available"] and not status["external"]
