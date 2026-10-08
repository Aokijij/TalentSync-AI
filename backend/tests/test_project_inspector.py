import io
import json
import stat
import zipfile
from types import SimpleNamespace

import pytest

from app.application.errors import UseCaseError
from app.infrastructure.project_inspector import (
    MAX_MANIFEST,
    MAX_UPLOAD,
    ProjectInspector,
)


def archive(files, compression=zipfile.ZIP_STORED):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as project:
        for name, content in files.items():
            project.writestr(name, content)
    return output.getvalue()


def inspect(blob):
    return ProjectInspector().inspect(SimpleNamespace(filename="project.zip", file=io.BytesIO(blob)))


def test_static_signals_do_not_read_sources_secrets_or_generated_dependencies():
    blob = archive({
        "project/src/private-client.py": "raise RuntimeError('never run'); secret='PRIVATE-CONTENT'",
        "project/src/main.ts": "SECRET-SOURCE",
        "project/.env": "SECRET-CREDENTIAL",
        "project/node_modules/vue/package.json": '{"dependencies":{"vue":"3"}}',
        "project/.venv/secret.py": "SECRET-VENV",
        "project/package.json": json.dumps({"dependencies": {"@angular/core": "20", "react": "19"},
            "scripts": {"postinstall": "NEVER-EXECUTE"}, "author": "PERSONAL-IDENTITY"}),
        "project/requirements-dev.txt": "fastapi[standard]>=0.1\npytest==8.3\n--extra-index-url SECRET-URL",
        "project/Dockerfile": "RUN malicious-command",
    })
    report = inspect(blob)
    skills = {row["skill"] for row in report["signals"]}
    assert skills == {"python", "typescript", "angular", "react", "fastapi", "pytest", "docker"}
    assert report["files_ignored"] == 3
    serialized = json.dumps(report)
    assert all(secret not in serialized for secret in ("PRIVATE", "SECRET", "NEVER-EXECUTE", "PERSONAL-IDENTITY", "private-client", "malicious-command"))
    assert "microservicios" not in skills and "vue" not in skills
    assert len(report["fingerprint"]) == 64 and report["manifests_read"] == 2


def test_python_metadata_and_maven_dependencies_are_separate_from_expertise():
    report = inspect(archive({
        "pyproject.toml": '[project]\ndependencies=["pandas>=2", "scikit_learn==1"]\n[project.optional-dependencies]\ntest=["pytest"]',
        "pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0"><dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency><dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency></dependencies></project>',
        "src/Main.java": "unread code",
    }))
    assert {row["skill"] for row in report["signals"]} == {"pandas", "scikit-learn", "pytest", "spring boot", "postgresql", "java"}
    assert "microservicios" not in {row["skill"] for row in report["signals"]}
    assert "autoría" in report["notice"]


@pytest.mark.parametrize("manifest,content", [
    ("package.json", "not-json"), ("pyproject.toml", "not = [valid"),
    ("package.json", "[" * 10000 + "]" * 10000),
    ("pom.xml", '<!DOCTYPE project [<!ENTITY data SYSTEM "file:///private">]><project>&data;</project>'),
])
def test_invalid_manifests_report_limits_without_parsing_entities(manifest, content):
    report = inspect(archive({manifest: content}))
    assert len(report["warnings"]) == 1 and report["signals"] == []


@pytest.mark.parametrize("name", ["../package.json", "/package.json", "C:/package.json", "folder\\package.json"])
def test_unsafe_paths_are_rejected_without_extracting(name):
    blob = archive({name: "{}"})
    if "\\" in name:
        # ZipInfo normalizes os.sep on Windows when writing. Patch the two header names.
        blob = blob.replace(b"folder/package.json", b"folder\\package.json")
    with pytest.raises(UseCaseError) as error:
        inspect(blob)
    assert error.value.status_code == 422


def test_links_duplicates_bombs_entry_count_and_manifest_size_are_bounded():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as project:
        link = zipfile.ZipInfo("package.json")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        project.writestr(link, "../private")
    invalid = [output.getvalue(), archive({"Package.json": "{}", "package.json": "{}"}),
               archive({"requirements.txt": "x" * 300000}, zipfile.ZIP_DEFLATED),
               archive({f"file-{index}.py": "" for index in range(2001)}),
               archive({"package.json": " " * (MAX_MANIFEST + 1)})]
    for blob in invalid:
        with pytest.raises(UseCaseError) as error:
            inspect(blob)
        assert error.value.status_code == 422


def test_upload_size_extension_and_corrupt_archive_are_rejected():
    with pytest.raises(UseCaseError) as error:
        inspect(b"x" * (MAX_UPLOAD + 1))
    assert error.value.status_code == 413
    with pytest.raises(UseCaseError):
        inspect(b"not a zip")
    with pytest.raises(UseCaseError):
        ProjectInspector().inspect(SimpleNamespace(filename="project.py", file=io.BytesIO(b"print('do not run')")))


def test_corrupt_deflate_stream_returns_validation_error():
    blob = bytearray(archive({"package.json": '{"dependencies":{"react":"19"}}'}, zipfile.ZIP_DEFLATED))
    # First local header has no extra fields; force a reserved DEFLATE block type.
    blob[30 + len(b"package.json")] = 0x07
    with pytest.raises(UseCaseError) as error:
        inspect(bytes(blob))
    assert error.value.status_code == 422
