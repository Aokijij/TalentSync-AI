"""Conservative static signals; declarations and filenames are not skill validation."""
import json
import re
import tomllib
from collections import Counter
from pathlib import PurePosixPath
from xml.etree import ElementTree

VERSION = "local-project-inspector-v1"
EXTENSIONS = {".py": "python", ".java": "java", ".js": "javascript", ".jsx": "javascript",
              ".ts": "typescript", ".tsx": "typescript", ".cs": "c#", ".go": "go",
              ".rs": "rust", ".php": "php", ".rb": "ruby", ".sql": "sql"}
NPM = {"@angular/core": "angular", "react": "react", "vue": "vue", "next": "nextjs",
       "express": "express", "typescript": "typescript", "jest": "jest", "vite": "vite",
       "@nestjs/core": "nestjs", "rxjs": "rxjs", "pg": "postgresql"}
PYTHON = {"fastapi": "fastapi", "django": "django", "flask": "flask", "numpy": "numpy",
          "pandas": "pandas", "scikit-learn": "scikit-learn", "pytest": "pytest", "torch": "pytorch",
          "tensorflow": "tensorflow", "sqlalchemy": "sqlalchemy"}


def manifest_kind(path):
    name = PurePosixPath(path).name.casefold()
    if name in {"package.json", "pyproject.toml", "pom.xml"}:
        return name
    if re.fullmatch(r"requirements(?:[-_.][a-z0-9_-]+)?\.txt", name):
        return "requirements.txt"
    return None


def analyze(files, manifests):
    """files are safe relative names; manifests are bounded bytes, never executed."""
    counts = Counter(EXTENSIONS[PurePosixPath(path).suffix.casefold()] for path in files
                     if PurePosixPath(path).suffix.casefold() in EXTENSIONS)
    sources, warnings = {}, set()

    def add(skill, kind, filename, dependency=None):
        source = {"kind": kind, "file": filename}
        if dependency:
            source["dependency"] = dependency
        rows = sources.setdefault(skill, [])
        if source not in rows and len(rows) < 4:
            rows.append(source)

    for skill in counts:
        add(skill, "file_extension", "tipo de archivo")
    if any(PurePosixPath(path).name.casefold() == "dockerfile" for path in files):
        add("docker", "build_file", "Dockerfile")
    for path, raw in manifests.items():
        kind = manifest_kind(path)
        try:
            text = raw.decode("utf-8-sig")
            if kind == "package.json":
                data = json.loads(text)
                for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    for name in data.get(field, {}):
                        if name in NPM:
                            add(NPM[name], "dependency", kind, name)
                if "node" in data.get("engines", {}):
                    add("nodejs", "runtime_declaration", kind)
            elif kind in {"requirements.txt", "pyproject.toml"}:
                if kind == "requirements.txt":
                    dependencies = text.splitlines()
                else:
                    data = tomllib.loads(text)
                    project = data.get("project", {})
                    dependencies = list(project.get("dependencies", []))
                    for group in project.get("optional-dependencies", {}).values():
                        dependencies.extend(group)
                    dependencies.extend(data.get("tool", {}).get("poetry", {}).get("dependencies", {}).keys())
                for dependency in dependencies:
                    match = re.match(r"^\s*([a-zA-Z0-9][a-zA-Z0-9_.-]*)", dependency)
                    name = re.sub(r"[-_.]+", "-", match[1].casefold()) if match else ""
                    if name in PYTHON:
                        add(PYTHON[name], "dependency", kind, name)
            elif kind == "pom.xml":
                if "<!doctype" in text.casefold() or "<!entity" in text.casefold():
                    raise ValueError("DTD not supported")
                root = ElementTree.fromstring(text)
                for node in root.iter():
                    if node.tag.rsplit("}", 1)[-1] not in {"dependency", "parent"}:
                        continue
                    values = {child.tag.rsplit("}", 1)[-1]: (child.text or "").strip() for child in node}
                    group, artifact = values.get("groupId"), values.get("artifactId", "")
                    if group == "org.springframework.boot" and artifact.startswith("spring-boot"):
                        add("spring boot", "dependency", kind, "org.springframework.boot")
                    elif group == "org.postgresql" and artifact == "postgresql":
                        add("postgresql", "dependency", kind, "org.postgresql:postgresql")
                    elif group == "org.junit.jupiter":
                        add("junit", "dependency", kind, "org.junit.jupiter")
        except (UnicodeError, ValueError, TypeError, AttributeError, RecursionError, ElementTree.ParseError):
            warnings.add(f"No se pudo interpretar un manifiesto {kind}; sus dependencias no se contabilizaron completamente.")
    return {"version": VERSION,
            "signals": [{"skill": skill, "source_files": counts[skill], "sources": sources[skill]}
                        for skill in sorted(sources)[:20]],
            "warnings": sorted(warnings),
            "notice": "La presencia de archivos o dependencias no demuestra autoría, funcionamiento ni dominio de una habilidad. No se ejecutó código."}
