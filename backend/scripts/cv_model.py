"""Explicit, verified download of the optional multilingual CV entity model."""
import argparse
import json
import time

import httpx

from scripts.local_model import ROOT, valid_file

FOLDER = ROOT / ".local/models/gliner_multi-v2.1"
SOURCES = (
    ("urchade/gliner_multi-v2.1", "443d26d654e0324125a96bebd8e796c14ff2efe6", "", ("gliner_config.json", "model.safetensors", "README.md")),
    ("microsoft/mdeberta-v3-base", "a0484667b22365f84929a935b5e50a51f71f159d", "encoder", ("config.json", "tokenizer_config.json", "spm.model")),
)


def prepare():
    if not FOLDER.resolve().is_relative_to((ROOT / ".local").resolve()):
        raise ValueError("El modelo debe permanecer dentro de .local")
    FOLDER.mkdir(parents=True, exist_ok=True)
    provenance = []
    with httpx.Client(trust_env=False, follow_redirects=True, timeout=httpx.Timeout(120, connect=20)) as client:
        for repository, revision, directory, names in SOURCES:
            response = client.get(f"https://huggingface.co/api/models/{repository}/revision/{revision}?blobs=true")
            response.raise_for_status()
            data = response.json()
            if data["sha"] != revision:
                raise ValueError("Unexpected model revision")
            entries = {row["rfilename"]: row for row in data["siblings"]}
            for name in names:
                metadata = entries[name]
                target = FOLDER / directory / name
                if not target.resolve().is_relative_to(FOLDER.resolve()) or not 0 < metadata["size"] <= (1_200_000_000 if name.endswith(".safetensors") else 10_000_000):
                    raise ValueError("Unexpected model file")
                target.parent.mkdir(parents=True, exist_ok=True)
                if not valid_file(target, metadata):
                    partial = target.with_suffix(target.suffix + ".partial")
                    if not partial.resolve().is_relative_to(FOLDER.resolve()):
                        raise ValueError("La descarga debe permanecer dentro del modelo")
                    print(f"Downloading {name}: {metadata['size']} bytes", flush=True)
                    with client.stream("GET", f"https://huggingface.co/{repository}/resolve/{revision}/{name}") as download:
                        download.raise_for_status()
                        received = 0
                        with partial.open("wb") as stream:
                            for chunk in download.iter_bytes(1024 * 1024):
                                received += len(chunk)
                                if received > metadata["size"]:
                                    raise ValueError("Download exceeds published size")
                                stream.write(chunk)
                    if not valid_file(partial, metadata):
                        raise ValueError(f"Invalid model fingerprint: {name}")
                    partial.replace(target)
                provenance.append({"repository": repository, "revision": revision, "name": str(target.relative_to(FOLDER)), **metadata})
    (FOLDER / "provenance.json").write_text(json.dumps({"license": "Apache-2.0", "files": provenance}, indent=2), encoding="utf-8")
    print("CV model downloaded and verified; activation remains explicit.")


def check():
    from app.core.config import settings
    from app.infrastructure.nlp.cv_entities import extract_entities
    started = time.perf_counter()
    text = "Experiencia laboral\nAnalista de datos en Acme Colombia. Usé Python.\nEducación\nIngeniería de sistemas, Universidad del Norte, 2015 - 2020."
    result = extract_entities(text, model_path=settings.cv_entity_model_path or str(FOLDER), python_path=settings.cv_entity_python or str(ROOT / ".local/cv-runtime/Scripts/python.exe"))
    if result["status"] != "ready" or not result["entities"]:
        raise ValueError("Falló la comprobación local del extractor de entidades")
    print(json.dumps({"method": result["method"], "status": result["status"], "entities": len(result["entities"]), "seconds": round(time.perf_counter() - started, 2)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "check"))
    args = parser.parse_args()
    prepare() if args.command == "prepare" else check()
