from types import SimpleNamespace

import pytest
from azure.core.exceptions import ResourceNotFoundError

from app.application.errors import UseCaseError
from app.infrastructure import images


def test_azure_images_survive_a_new_instance_without_local_disk(monkeypatch, tmp_path):
    blobs = {}

    def upload_blob(**kwargs):
        assert kwargs["overwrite"] is False
        assert kwargs["content_settings"].content_type == "image/png"
        blobs[kwargs["name"]] = kwargs["data"]

    container = SimpleNamespace(upload_blob=upload_blob, download_blob=lambda name: SimpleNamespace(readall=lambda: blobs[name]))
    monkeypatch.setattr(images, "blob_container", lambda *args: container)
    first = images.ImageStorage(str(tmp_path / "replica-one"), "https://storage.example", "cvs")
    first.save("profile_photos", "user_1_unique.png", b"image", "image/png")
    second = images.ImageStorage(str(tmp_path / "replica-two"), "https://storage.example", "cvs")
    assert second.read("profile_photos", "user_1_unique.png") == b"image"
    assert not (tmp_path / "replica-one").exists()
    assert not (tmp_path / "replica-two").exists()


@pytest.mark.parametrize("exception,expected", [(ResourceNotFoundError("missing"), 404), (RuntimeError("private service details"), 503)])
def test_azure_image_errors_are_safe(monkeypatch, tmp_path, exception, expected):
    def fail(*args, **kwargs):
        raise exception

    monkeypatch.setattr(images, "blob_container", fail)
    storage = images.ImageStorage(str(tmp_path), "https://storage.example", "cvs")
    with pytest.raises(UseCaseError) as error:
        storage.read("profile_photos", "missing.png")
    assert error.value.status_code == expected
    assert "private service details" not in error.value.detail
    with pytest.raises(UseCaseError) as error:
        storage.save("profile_photos", "new.png", b"image", "image/png")
    assert error.value.status_code == 503
    assert not list(tmp_path.iterdir())


def test_local_storage_reads_existing_names_and_missing_files(tmp_path):
    storage = images.ImageStorage(str(tmp_path), None, "cvs")
    storage.save("profile_photos", "user_1.png", b"legacy-photo", "image/png")
    assert storage.read("profile_photos", "user_1.png") == b"legacy-photo"
    with pytest.raises(UseCaseError) as error:
        storage.read("profile_photos", "missing.png")
    assert error.value.status_code == 404
