import importlib.util
import json
from pathlib import Path

import httpx
import pytest

from app.application.ports.services import MailDeliveryError

spec = importlib.util.spec_from_file_location("local_resend_test", Path(__file__).resolve().parents[2] / "scripts/resend_test.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


@pytest.fixture
def config(tmp_path):
    path = tmp_path / "resend.env"
    path.write_text("RESEND_TEST_ENABLED=true\nRESEND_API_KEY=re_PRIVATE\nRESEND_FROM=onboarding@resend.dev\nRESEND_TEST_RECIPIENT=authorized@example.com\n", encoding="utf-8")
    return path


def test_smoke_only_authorized_recipient_no_second_send(config, tmp_path, monkeypatch):
    config.write_text(config.read_text(), encoding="utf-8-sig")  # Windows dotenv BOM.
    monkeypatch.setenv("RESEND_TEST_RECIPIENT", "other@example.com")
    requests = []
    def handle(request):
        requests.append(request)
        assert json.loads(request.content)["to"] == ["authorized@example.com"]
        return httpx.Response(200, json={"id": "accepted"})
    state = tmp_path / "state.json"
    transport = httpx.MockTransport(handle)
    assert smoke.run_test(config, state, transport=transport, now=100) == "accepted"
    assert smoke.run_test(config, state, transport=transport, now=200000) == "already_accepted"
    assert len(requests) == 1
    assert "re_PRIVATE" not in state.read_text()


@pytest.mark.parametrize("change", [
    ("RESEND_TEST_ENABLED=true", "RESEND_TEST_ENABLED=false"),
    ("re_PRIVATE", ""),
    ("authorized@example.com", ""),
    ("authorized@example.com", "first@example.com,second@example.com"),
    ("onboarding@resend.dev", "sender@example.com"),
])
def test_invalid_config_never_sends(config, tmp_path, change):
    config.write_text(config.read_text().replace(*change))
    def reject(request):
        pytest.fail("Invalid configuration must never reach Resend")
    with pytest.raises(ValueError) as error:
        smoke.run_test(config, tmp_path / "state.json", transport=httpx.MockTransport(reject))
    assert "PRIVATE" not in str(error.value)


def test_timeout_retry_same_id_and_expired_attempt_never_sends(config, tmp_path):
    requests = []
    def handle(request):
        requests.append(request)
        raise httpx.ReadTimeout("PRIVATE provider error")
    state = tmp_path / "state.json"
    transport = httpx.MockTransport(handle)
    for now in [100, 200]:
        with pytest.raises(MailDeliveryError):
            smoke.run_test(config, state, transport=transport, now=now)
    assert requests[0].headers["Idempotency-Key"] == requests[1].headers["Idempotency-Key"]
    assert "PRIVATE" not in state.read_text()
    with pytest.raises(ValueError):
        smoke.run_test(config, state, transport=transport, now=100000)
    assert len(requests) == 2


def test_changed_destination_and_concurrent_run_blocked(config, tmp_path):
    state = tmp_path / "state.json"
    transport = httpx.MockTransport(lambda request: httpx.Response(200))
    smoke.run_test(config, state, transport=transport)
    config.write_text(config.read_text().replace("authorized@example.com", "other@example.com"))
    with pytest.raises(ValueError):
        smoke.run_test(config, state, transport=transport)
    state.with_suffix(".lock").touch()
    with pytest.raises(ValueError):
        smoke.run_test(config, state, transport=transport)
