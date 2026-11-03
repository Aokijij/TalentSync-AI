# ruff: noqa: F811
import base64
import hashlib
import hmac
import time

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.infrastructure.interview_ice import InterviewIce


def configured(**fields):
    return Settings(_env_file=None, secret_key="x" * 48, **fields)


@pytest.mark.parametrize("fields", [
    {"webrtc_stun_urls": ["https://stun.example.com"]},
    {"webrtc_stun_urls": ["stun:server.example.com?transport=udp"]},
    {"webrtc_turn_urls": ["turn:user:password@server.example.com"]},
    {"webrtc_turn_urls": ["turn:server.example.com:99999"]},
    {"webrtc_turn_urls": ["turn:server.example.com/path"]},
    {"webrtc_turn_urls": ["turn:server.example.com?token=secret"]},
    {"webrtc_turn_urls": ["turn:server.example.com"]},
    {"webrtc_relay_only": True},
])
def test_ice_rejects_invalid_or_incomplete_configuration(fields):
    with pytest.raises(ValidationError):
        configured(**fields)


def test_ice_credentials_expire_and_hide_identifiers():
    config = configured(webrtc_stun_urls=["stun:localhost:3478"],
        webrtc_turn_urls=["turn:localhost:3478?transport=udp", "turns:localhost:5349?transport=tcp"],
        webrtc_turn_secret="secret" * 8, webrtc_relay_only=True)
    issuer = InterviewIce(config)
    first = issuer.configuration("room-sensitive-id", "user-sensitive-id")
    second = issuer.configuration("room-sensitive-id", "user-sensitive-id")
    assert first["mode"] == "turn_configured"
    assert first["ice_transport_policy"] == "relay"
    assert int(time.time()) + 3590 <= first["expires_at"] <= int(time.time()) + 3601
    credentials = first["ice_servers"][1]
    assert credentials["username"].startswith(str(first["expires_at"]) + ":")
    assert "sensitive" not in credentials["username"]
    expected = base64.b64encode(hmac.new(config.webrtc_turn_secret.encode(), credentials["username"].encode(), hashlib.sha1).digest()).decode()
    assert credentials["credential"] == expected
    assert credentials != second["ice_servers"][1]
    assert config.webrtc_turn_secret not in str(first)
    assert InterviewIce(configured()).configuration("room", 1) == {
        "ice_servers": [], "ice_transport_policy": "all", "expires_at": None, "mode": "direct"}


