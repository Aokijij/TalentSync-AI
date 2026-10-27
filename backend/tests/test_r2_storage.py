# ruff: noqa: F811
import io
from hashlib import sha256
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from pydantic import ValidationError
from test_api_flows import client, register  # noqa: F401

from app.application.errors import UseCaseError
from app.core.config import Settings
from app.infrastructure import images, private_account_files
from app.infrastructure.nlp import resumes
from app.infrastructure.r2_storage import (
    MAX_OBJECT_BYTES,
    R2Storage,
    StoredObject,
    _storage,
)

ENDPOINT = "https://" + "a" * 32 + ".r2.cloudflarestorage.com"
BUCKET = "talentsync-private-test"


def config(**changes):
    return Settings(_env_file=None, secret_key="test-only-" * 6,
                    **({"r2_endpoint_url": ENDPOINT, "r2_bucket": BUCKET,
                        "r2_access_key_id": "test-access", "r2_secret_access_key": "test-secret"} | changes))


class MemoryS3:
    """No network. Keep preconditions and paginated prefixes observable."""
    def __init__(self):
        self.objects = {}
        self.calls = []

    def put_object(self, **params):
        self.calls.append(("put", params))
        key = params["Key"]
        if params.get("IfNoneMatch") == "*" and key in self.objects:
            raise ClientError({"Error": {"Code": "PreconditionFailed", "Message": "PRIVATE DETAILS"}}, "PutObject")
        self.objects[key] = params["Body"]
        return {}

    def get_object(self, **params):
        self.calls.append(("get", params))
        key = params["Key"]
        if key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "PRIVATE DETAILS"}}, "GetObject")
        value = self.objects[key]
        etag = '"' + sha256(value).hexdigest() + '"'
        if params.get("IfMatch", etag) != etag:
            raise ClientError({"Error": {"Code": "PreconditionFailed", "Message": "PRIVATE DETAILS"}}, "GetObject")
        return {"Body": StreamingBody(io.BytesIO(value), len(value)), "ContentLength": len(value)}

    def list_objects_v2(self, **params):
        self.calls.append(("list", params))
        keys = sorted(key for key in self.objects if key.startswith(params["Prefix"]))
        start = int(params.get("ContinuationToken", "0"))
        count = min(1, params["MaxKeys"])
        selected = keys[start:start + count]
        return {"Contents": [{"Key": key, "Size": len(self.objects[key]), "ETag": '"' + sha256(self.objects[key]).hexdigest() + '"'} for key in selected],
                "IsTruncated": start + count < len(keys), "NextContinuationToken": str(start + count)}

    def delete_object(self, **params):
        self.calls.append(("delete", params))
        self.objects.pop(params["Key"], None)
        return {}


@pytest.mark.parametrize("changes", [
    {"r2_access_key_id": ""}, {"r2_secret_access_key": ""}, {"r2_bucket": ""},
    {"r2_endpoint_url": ""}, {"r2_endpoint_url": "http://127.0.0.1:8000"},
    {"r2_endpoint_url": ENDPOINT + "/bucket"}, {"r2_endpoint_url": ENDPOINT + "?private=secret"},
    {"r2_endpoint_url": ENDPOINT.replace("https://", "https://user:secret@")},
    {"r2_endpoint_url": "https://evil.r2.cloudflarestorage.com.example.com"},
    {"r2_bucket": "Invalid Name"}, {"r2_secret_access_key": "SECRET VALUE"},
    {"azure_storage_account_url": "https://account.blob.core.windows.net"},
])
def test_incomplete_insecure_or_conflicting_storage_fails_before_requests(changes):
    with pytest.raises(ValidationError) as error:
        config(**changes)
    assert "input_value" not in str(error.value) and "test-secret" not in str(error.value)


def test_s3_client_is_private_scoped_and_has_bounded_timeouts():
    values = config()
    assert "test-secret" not in repr(values) and "test-access" not in repr(values)
    store = _storage(ENDPOINT, BUCKET, "auto", "test-access", "test-secret")
    assert store.client.meta.endpoint_url == ENDPOINT and store.bucket == BUCKET
    assert store.client.meta.config.signature_version == "s3v4"
    assert store.client.meta.config.connect_timeout == 3 and store.client.meta.config.read_timeout == 10
    assert store.client.meta.config.retries["total_max_attempts"] == 2


def test_images_survive_replica_change_without_local_files_and_cannot_overwrite(tmp_path):
    client = MemoryS3()
    store = R2Storage(client, BUCKET)
    first = images.ImageStorage(str(tmp_path / "first"), None, "unused", r2=store)
    second = images.ImageStorage(str(tmp_path / "second"), None, "unused", r2=store)
    first.save("profile_photos", "user_1_photo.png", b"image", "image/png")
    assert second.read("profile_photos", "user_1_photo.png") == b"image"
    put = next(params for method, params in client.calls if method == "put")
    assert put["Bucket"] == BUCKET and put["IfNoneMatch"] == "*"
    assert put["StorageClass"] == "STANDARD" and put["CacheControl"] == "private, no-store"
    assert "ACL" not in put
    with pytest.raises(UseCaseError):
        second.save("profile_photos", "user_1_photo.png", b"replacement", "image/png")
    assert second.read("profile_photos", "user_1_photo.png") == b"image"
    assert not list(tmp_path.iterdir())


def test_cloud_failure_never_falls_back_to_old_local_document(tmp_path):
    directory = tmp_path / "profile_photos"
    directory.mkdir()
    (directory / "user_1.png").write_bytes(b"stale private photo")
    class Unavailable:
        def get_object(self, **params):
            raise ClientError({"Error": {"Code": "AccessDenied", "Message": "PRIVATE SECRET AND URL"}}, "GetObject")
    image = images.ImageStorage(str(tmp_path), None, "unused", r2=R2Storage(Unavailable(), BUCKET))
    with pytest.raises(UseCaseError) as error:
        image.read("profile_photos", "user_1.png")
    assert error.value.status_code == 503 and "SECRET" not in error.value.detail
    missing = images.ImageStorage(str(tmp_path), None, "unused", r2=R2Storage(MemoryS3(), BUCKET))
    with pytest.raises(UseCaseError) as error:
        missing.read("profile_photos", "user_1.png")
    assert error.value.status_code == 404


def test_large_download_closes_body_without_reading_it():
    body = io.BytesIO(b"never read")
    client = SimpleNamespace(get_object=lambda **params: {"ContentLength": MAX_OBJECT_BYTES + 1, "Body": body})
    with pytest.raises(OSError):
        R2Storage(client, BUCKET).read("users/1/cv.pdf")
    assert body.closed


@pytest.mark.parametrize("key", ["../cv.pdf", "/users/1/cv.pdf", "users//cv.pdf", "users/../cv.pdf", "users\\1\\cv.pdf"])
def test_invalid_object_paths_never_reach_s3(key):
    client = MemoryS3()
    with pytest.raises(ValueError):
        R2Storage(client, BUCKET).read(key)
    assert not client.calls


def test_paginated_export_and_erasure_preserve_other_owners_and_company_files(monkeypatch, tmp_path):
    client = MemoryS3()
    client.objects = {"users/1/cv.pdf": b"%PDF-first", "users/1/other.pdf": b"%PDF-second",
                      "profile_photos/user_1_photo.png": b"image", "users/10/cv.pdf": b"%PDF-other",
                      "profile_photos/user_10_photo.png": b"other photo", "company_images/company_1_logo.png": b"logo"}
    store = R2Storage(client, BUCKET)
    monkeypatch.setattr(private_account_files, "get_r2_storage", lambda config: store)
    files = private_account_files.PrivateAccountFiles(SimpleNamespace(upload_dir=str(tmp_path), azure_storage_account_url=""))
    exported = files.export(1)
    assert {content for _, content in exported} == {b"%PDF-first", b"%PDF-second", b"image"}
    assert all(params.get("IfMatch") for method, params in client.calls if method == "get")
    files.erase(1)
    assert set(client.objects) == {"users/10/cv.pdf", "profile_photos/user_10_photo.png", "company_images/company_1_logo.png"}


def test_unexpected_owner_or_too_many_objects_blocks_deletion(monkeypatch, tmp_path):
    client = MemoryS3()
    client.list_objects_v2 = lambda **params: {"Contents": [{"Key": "users/10/cv.pdf", "Size": 1, "ETag": "etag"}]}
    store = R2Storage(client, BUCKET)
    monkeypatch.setattr(private_account_files, "get_r2_storage", lambda config: store)
    files = private_account_files.PrivateAccountFiles(SimpleNamespace(upload_dir=str(tmp_path), azure_storage_account_url=""))
    with pytest.raises(OSError):
        files.erase(1)
    assert all(method != "delete" for method, _ in client.calls)
    client = MemoryS3()
    client.objects = {f"users/1/{index}.pdf": b"file" for index in range(3)}
    with pytest.raises(OSError):
        R2Storage(client, BUCKET).list_prefix("users/1/", limit=2)


def test_export_size_limit_is_checked_before_downloading(monkeypatch, tmp_path):
    def no_read(*args, **kwargs):
        pytest.fail("Oversize object must not be downloaded")
    store = SimpleNamespace(list_prefix=lambda prefix, **params: [StoredObject("users/1/huge.pdf", private_account_files.MAX_EXPORT + 1, "etag")] if prefix.startswith("users/") else [], read=no_read)
    monkeypatch.setattr(private_account_files, "get_r2_storage", lambda config: store)
    with pytest.raises(OSError):
        private_account_files.PrivateAccountFiles(SimpleNamespace(upload_dir=str(tmp_path), azure_storage_account_url="")).export(1)


def test_cv_upload_uses_temporary_pdf_then_persists_and_reads_owner_object(monkeypatch, tmp_path):
    client = MemoryS3()
    store = R2Storage(client, BUCKET)
    monkeypatch.setattr(resumes, "get_r2_storage", lambda: store)
    monkeypatch.setattr(resumes.settings, "upload_dir", str(tmp_path))
    seen = []
    def extract(path):
        from pathlib import Path
        seen.append(Path(path))
        assert Path(path).read_bytes() == b"%PDF-test"
        return "Python y SQL"
    monkeypatch.setattr(resumes, "extract_pdf_text", extract)
    reader = resumes.ResumeReader()
    upload = SimpleNamespace(filename="Mi currículum.pdf", content_type="application/pdf", file=io.BytesIO(b"%PDF-test"))
    name, text = reader.extract(upload, 1)
    assert name == "Mi_currículum.pdf" and text == "Python y SQL"
    assert all(not path.exists() for path in seen) and not list(tmp_path.iterdir())
    assert reader.original(SimpleNamespace(cv_filename=name, user_id=1)) == b"%PDF-test"
    assert reader.storage_available()
    with pytest.raises(UseCaseError) as error:
        reader.original(SimpleNamespace(cv_filename=name, user_id=10))
    assert error.value.status_code == 404
    assert next(params for method, params in client.calls if method == "put")["ContentType"] == "application/pdf"


def test_cv_extraction_failure_cleans_temporary_file_without_upload(monkeypatch):
    from pathlib import Path
    client = MemoryS3()
    monkeypatch.setattr(resumes, "get_r2_storage", lambda: R2Storage(client, BUCKET))
    seen = []
    def invalid(path):
        seen.append(Path(path))
        raise ValueError("Synthetic unreadable PDF")
    monkeypatch.setattr(resumes, "extract_pdf_text", invalid)
    with pytest.raises(UseCaseError):
        resumes.ResumeReader().extract(SimpleNamespace(filename="cv.pdf", content_type="application/pdf", file=io.BytesIO(b"%PDF-bad")), 1)
    assert all(not path.exists() for path in seen) and not client.objects


def test_r2_readiness_does_not_report_success_on_access_denied(monkeypatch):
    client = MemoryS3()
    def denied(**params):
        raise ClientError({"Error": {"Code": "AccessDenied", "Message": "PRIVATE"}}, "ListObjectsV2")
    client.list_objects_v2 = denied
    monkeypatch.setattr(resumes, "get_r2_storage", lambda: R2Storage(client, BUCKET))
    assert not resumes.ResumeReader().storage_available()


def test_r2_photo_routes_and_account_export_keep_owner_authorization(client, monkeypatch):
    import zipfile

    store = R2Storage(MemoryS3(), BUCKET)
    monkeypatch.setattr(images, "get_r2_storage", lambda: store)
    monkeypatch.setattr(private_account_files, "get_r2_storage", lambda config: store)
    person, own = register(client, "r2-photo-owner")
    _, other = register(client, "r2-photo-other")
    photo = b"\x89PNG\r\n\x1a\nsynthetic"
    result = client.post("/api/v1/profiles/me/photo", headers=own, files={"file": ("photo.png", photo, "image/png")})
    assert result.status_code == 200, result.text
    endpoint = f"/api/v1/profiles/{person['id']}/photo"
    assert client.get(endpoint).status_code == 401
    assert client.get(endpoint, headers=other).status_code == 403
    response = client.get(endpoint, headers=own)
    assert response.content == photo and "no-store" in response.headers["cache-control"]
    response = client.post("/api/v1/account/data/export", headers=own, json={"password": "Test-password-2026!"})
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert any(archive.read(name) == photo for name in archive.namelist() if name.startswith("files/"))
    response = client.post("/api/v1/account/data/erase", headers=own, json={"password": "Test-password-2026!", "confirmation": "ELIMINAR"})
    assert response.status_code == 200 and not response.json()["files_pending"]
    assert not store.client.objects
