"""Conservative name resolution. Affinity rules are internal, never diploma equivalences."""

import hashlib
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path


def academic_name(value):
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = " ".join(re.findall(r"[a-z0-9]+", text))
    # Remove qualification prefixes only; the level is evaluated independently.
    return re.sub(
        r"^(?:tecnic[oa](?: profesional)?|tecnolog[oa]|tecnologia|profesional universitari[oa]|profesional|licenciad[oa]|licenciatura|maestria|especializacion|doctorado) (?:en |de )?",
        "",
        text,
    ).strip()


@lru_cache(maxsize=1)
def catalog():
    return json.loads(
        (Path(__file__).parents[1] / "data/academic_fields.json").read_text(
            encoding="utf-8"
        )
    )


@lru_cache(maxsize=1)
def catalog_fingerprint():
    return hashlib.sha256(
        json.dumps(catalog(), sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


@lru_cache(maxsize=1)
def alias_index():
    return {
        academic_name(alias): row
        for row in catalog()["programs"]
        for alias in [row["label"], *row["aliases"]]
    }


def resolve_program(value):
    return alias_index().get(academic_name(value))


def compare_fields(candidate, requested, policy="related"):
    left, right = academic_name(candidate), academic_name(requested)
    base = {"candidate_degree": candidate, "requested_field": requested}
    if left and left == right:
        return {
            **base,
            "status": "exact",
            "score": 100,
            "reason": "Misma denominación de formación, normalizada.",
        }
    a, b = resolve_program(candidate), resolve_program(requested)
    if a and b and a["id"] == b["id"]:
        return {
            **base,
            "status": "name_variant",
            "score": 100,
            "reason": f"Variantes de nombre del área «{a['label']}» en el catálogo interno; el nivel se revisa aparte.",
        }
    if not a or not b:
        return {
            **base,
            "status": "review",
            "score": None,
            "reason": "Una denominación no está reconocida. Requiere revisión; no se declara incompatible por su nombre.",
        }
    related = any(
        {a["id"], b["id"]} == set(pair) for pair in catalog()["related_pairs"]
    )
    if related:
        return {
            **base,
            "status": "related" if policy == "related" else "not_accepted",
            "score": 70 if policy == "related" else 0,
            "reason": "Relación registrada por TalentSync entre dos áreas distintas. "
            + (
                "Aporta afinidad parcial; no equivale al título solicitado."
                if policy == "related"
                else "La empresa admite solo las áreas seleccionadas y sus variantes de nombre."
            ),
        }
    return {
        **base,
        "status": "unrelated",
        "score": 0,
        "reason": "Áreas reconocidas sin una relación admitida en el catálogo. La empresa puede añadir ambas como alternativas.",
    }
