"""Explicit public model preparation; inference never downloads files."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import httpx

REPOSITORY = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
FILES = (
    "1_Pooling/config.json", "README.md", "config.json", "config_sentence_transformers.json",
    "model.safetensors", "modules.json", "sentence_bert_config.json", "sentencepiece.bpe.model",
    "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json", "unigram.json",
)
ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / ".local/models/paraphrase-multilingual-MiniLM-L12-v2"


def valid_file(path, metadata):
    if not path.is_file() or path.stat().st_size != metadata["size"]:
        return False
    large = metadata.get("lfs")
    digest = hashlib.sha256() if large else hashlib.sha1()
    if not large:
        digest.update(f"blob {metadata['size']}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == (large["sha256"] if large else metadata["blobId"])


def prepare():
    FOLDER.mkdir(parents=True, exist_ok=True)
    if not FOLDER.resolve().is_relative_to((ROOT / ".local").resolve()):
        raise ValueError("La carpeta debe permanecer dentro de .local")
    # No account tokens, inherited proxies, remote Python, pickle or automatic activation.
    with httpx.Client(timeout=httpx.Timeout(60, connect=15), trust_env=False, follow_redirects=True) as client:
        response = client.get(f"https://huggingface.co/api/models/{REPOSITORY}/revision/{REVISION}?blobs=true")
        response.raise_for_status()
        info = response.json()
        if info["sha"] != REVISION:
            raise ValueError("La revisión recibida no coincide con la fijada")
        entries = {row["rfilename"]: row for row in info["siblings"]}
        records = []
        for name in FILES:
            metadata = entries[name]
            if not 0 < metadata["size"] <= (600_000_000 if name == "model.safetensors" else 25_000_000):
                raise ValueError("Tamaño de archivo inesperado")
            target = FOLDER / name
            if not target.resolve().is_relative_to(FOLDER.resolve()):
                raise ValueError("La ruta no puede salir del modelo")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not valid_file(target, metadata):
                partial = target.with_name(target.name + ".partial")
                if not partial.resolve().is_relative_to(FOLDER.resolve()):
                    raise ValueError("La descarga debe permanecer dentro del modelo")
                print(f"Descargando {name} ({metadata['size']} bytes)...", flush=True)
                with client.stream("GET", f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}") as download:
                    download.raise_for_status()
                    received = 0
                    with partial.open("wb") as stream:
                        for chunk in download.iter_bytes(1024 * 1024):
                            received += len(chunk)
                            if received > metadata["size"]:
                                raise ValueError("La descarga excede el tamaño publicado")
                            stream.write(chunk)
                if not valid_file(partial, metadata):
                    raise ValueError(f"No coincide la huella publicada de {name}")
                partial.replace(target)
            records.append({"name": name, "size": metadata["size"], "sha256": metadata.get("lfs", {}).get("sha256"), "git_blob": metadata["blobId"]})
    provenance = {"repository": REPOSITORY, "revision": REVISION, "license": "Apache-2.0", "files": records}
    (FOLDER.parent / "minilm-provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Modelo verificado: {FOLDER}\nNo se ha cambiado MATCH_MODEL_PATH.")


def check():
    from app.infrastructure.nlp.matching_encoder import LocalMatchingEncoder

    started = time.perf_counter()
    encoder = LocalMatchingEncoder(str(FOLDER))
    examples = {
        "identical": ("Desarrollo de APIs con Python", "Desarrollo de APIs con Python"),
        "translated": ("Desarrollo de aplicaciones web", "Web application development"),
        "unrelated": ("Desarrollo de aplicaciones web", "Cultivo de flores y cuidado de jardines"),
    }
    scores = {key: encoder.similarity(*texts) for key, texts in examples.items()}
    if scores["identical"] < 99 or scores["translated"] <= scores["unrelated"]:
        raise ValueError("Falló la comprobación semántica básica")
    print(json.dumps({"method": encoder.method, "scores": scores, "seconds": round(time.perf_counter() - started, 2)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Pesos públicos fijados y comprobación local de MiniLM")
    parser.add_argument("command", choices=("prepare", "check"))
    args = parser.parse_args()
    prepare() if args.command == "prepare" else check()


if __name__ == "__main__":
    main()
