"""Isolated optional GLiNER runtime; JSON over pipes, no CV persistence/network."""
import contextlib
import json
import os
import sys
from pathlib import Path


def load_model(folder):
    import torch
    from gliner import GLiNER
    from safetensors.torch import load_file
    from transformers import AutoTokenizer
    torch.set_num_threads(2)
    config = json.loads((folder / "gliner_config.json").read_text(encoding="utf-8"))
    config["model_name"] = str(folder / "encoder")
    tokenizer = AutoTokenizer.from_pretrained(str(folder / "encoder"), local_files_only=True, trust_remote_code=False)
    tokenizer.model_max_length = 512
    config = GLiNER._config_from_dict(config)
    model_class = GLiNER._get_gliner_class(config)
    with torch.device("meta"):
        model = model_class(config, tokenizer=tokenizer, backbone_from_pretrained=False, local_files_only=True)
        model._resize_token_embeddings(model, model.config, tokenizer)
    model.model.load_state_dict(load_file(str(folder / "model.safetensors"), device="cpu"), strict=True, assign=True)
    _, unsupported = model._materialize_meta_buffers(model.model)
    if unsupported or any(parameter.is_meta for parameter in model.model.parameters()):
        raise ValueError("Unsupported local model buffers")
    return model.eval()


def main():
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    def deny_network(event, args):
        if event in {"socket.connect", "socket.getaddrinfo"}:
            raise RuntimeError("Network disabled in CV inference")
    sys.addaudithook(deny_network)
    # This file is executed directly in the isolated interpreter.
    sys.path.insert(0, str(Path(__file__).parent))
    from cv_entities import LABELS, MAX_CHARS, chunks
    payload = json.loads(sys.stdin.read(200_000))
    text = payload["text"][:MAX_CHARS]
    with contextlib.redirect_stdout(sys.stderr):
        model = load_model(Path(sys.argv[1]))
        entities = []
        for offset, chunk in chunks(text):
            for row in model.predict_entities(chunk, list(LABELS), threshold=.5):
                entities.append({**row, "start": row["start"] + offset, "end": row["end"] + offset})
    sys.stdout.write(json.dumps({"entities": entities}, ensure_ascii=False))


if __name__ == "__main__":
    main()
