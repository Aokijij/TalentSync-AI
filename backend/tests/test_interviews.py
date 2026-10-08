# ruff: noqa: F811
import pytest
from test_api_flows import client, register  # noqa: F401


@pytest.mark.parametrize("method,path", [
    ("get", "/interviews/rooms"), ("post", "/interviews/rooms"),
    ("get", "/interviews/rooms/old-room"), ("put", "/interviews/rooms/old-room"),
    ("post", "/interviews/rooms/old-room/close"),
    ("get", "/matching/projects/options"), ("post", "/matching/projects/preview"),
    ("post", "/matching/projects/github/preview"), ("post", "/matching/projects/evidence"),
])
def test_retired_capabilities_have_no_http_entry_point(client, method, path):
    _, headers = register(client, "retired-features")
    assert getattr(client, method)("/api/v1" + path, headers=headers).status_code == 404
