"""Offline, aggregate pilot scoring. Does not read CVs, contact providers or change models."""
import argparse
import json
import math
import re
import unicodedata
from pathlib import Path


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def f1(expected, actual):
    expected, actual = {normalized(value) for value in expected}, {normalized(value) for value in actual}
    precision = len(expected & actual) / len(actual) if actual else float(not expected)
    recall = len(expected & actual) / len(expected) if expected else 1.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def ndcg(labels, ranking, k=5):
    def dcg(values):
        return sum((2 ** value - 1) / math.log2(index + 2) for index, value in enumerate(values[:k]))
    ideal = dcg(sorted(labels.values(), reverse=True))
    return dcg([labels[identifier] for identifier in ranking]) / ideal if ideal else 0.0


def evaluate(data):
    synthetic = data.get("mode") == "synthetic"
    if data.get("mode") not in {"synthetic", "consented_pilot"}:
        raise ValueError("Indica synthetic o consented_pilot")
    if not synthetic and not (data.get("consent", {}).get("documented") is True and data.get("consent", {}).get("withdrawal_available") is True):
        raise ValueError("El piloto requiere consentimiento documentado y posibilidad de retirada")
    samples = data.get("samples", [])
    if not isinstance(samples, list) or not 1 <= len(samples) <= 10000:
        raise ValueError("Se requieren de 1 a 10000 muestras")
    extraction, ranking, completion, roles, seen = [], [], [], {}, set()
    for row in samples:
        identifier = row.get("id", "")
        if not re.fullmatch(r"S[0-9]{3,8}", identifier) or identifier in seen:
            raise ValueError("Usa identificadores únicos S001, sin nombres ni correos")
        seen.add(identifier)
        role = row.get("role")
        if role not in {"candidate", "company", "admin"}:
            raise ValueError("Rol de evaluación inválido")
        roles[role] = roles.get(role, 0) + 1
        if type(row.get("flow_completed")) is not bool:
            raise ValueError("Registra si se completó el recorrido")
        completion.append(float(row["flow_completed"]))
        fields = row.get("extraction", {})
        for field, value in fields.items():
            if field not in {"skills", "education", "experience", "languages"} or not isinstance(value, dict):
                raise ValueError("Campo de extracción inválido")
            if set(value) != {"expected", "actual"} or any(not isinstance(values, list) or len(values) > 100 or any(not isinstance(item, str) or len(item) > 200 for item in values) for values in value.values()):
                raise ValueError("Extracción requiere listas expected y actual acotadas")
            extraction.append(f1(value["expected"], value["actual"]))
        labels, ordered = row.get("relevance", {}), row.get("ranking", [])
        if labels:
            if not isinstance(labels, dict) or len(labels) > 500 or any(not re.fullmatch(r"J[0-9]{3,8}", key) or type(value) is not int or not 0 <= value <= 3 for key, value in labels.items()):
                raise ValueError("Relevancia: J001 con valoración de 0 a 3")
            if not isinstance(ordered, list) or not ordered or any(key not in labels for key in ordered) or len(set(ordered)) != len(ordered):
                raise ValueError("Orden de vacantes inválido o repetido")
            if not any(labels.values()):
                raise ValueError("Incluye al menos una vacante relevante")
            ranking.append(ndcg(labels, ordered))
    critical = data.get("critical_issues")
    if type(critical) is not int or critical < 0:
        raise ValueError("Registra el número de incidencias críticas")
    mean = lambda values: round(sum(values) / len(values), 4) if values else None
    metrics = {"extraction_f1": mean(extraction), "ranking_ndcg_at_5": mean(ranking), "flow_completion": mean(completion)}
    sufficient = len(samples) >= 20 and all(roles.get(role, 0) >= 5 for role in ("candidate", "company", "admin")) and len(extraction) >= 20 and len(ranking) >= 10
    passing = sufficient and critical == 0 and (metrics["extraction_f1"] or 0) >= .9 and (metrics["ranking_ndcg_at_5"] or 0) >= .8 and metrics["flow_completion"] >= .9
    return {"schema": 1, "mode": data["mode"], "status": "synthetic_example" if synthetic else "review_ready" if passing else "needs_review",
            "samples": len(samples), "roles": roles, "extraction_fields": len(extraction), "ranked_samples": len(ranking), "metrics": metrics,
            "critical_issues": critical, "minimum_sample_reached": sufficient, "real_world_validated": False,
            "note": "Ejemplo sintético: no valida calidad con personas reales." if synthetic else "Requiere revisión humana, acuerdo entre evaluadores y revisión de sesgos por área. No activa modelos ni autoriza despliegues."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("La salida debe ser distinta de la entrada")
    if args.input.stat().st_size > 5_000_000:
        parser.error("La entrada supera 5 MB")
    try:
        result = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    except (ValueError, TypeError, KeyError, AttributeError):
        parser.error("Entrada inválida: consulta docs/PROTOCOLO_PILOTO.md; no se muestran sus datos")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Evaluación agregada: {result['status']}; {result['samples']} muestras")


if __name__ == "__main__":
    main()
