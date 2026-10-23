"""Local readiness/load and synthetic private-file recovery rehearsal. No deployment."""
import argparse
import hashlib
import http.client
import json
import math
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def probe(base, route):
    address = urlsplit(base)
    connection_class = http.client.HTTPSConnection if address.scheme == "https" else http.client.HTTPConnection
    connection = connection_class(address.hostname, address.port, timeout=10)
    start = time.perf_counter()
    try:
        connection.request("GET", route, headers={"Accept": "application/json"})
        response = connection.getresponse()
        body = response.read(65536)
        return {"status": response.status, "milliseconds": (time.perf_counter() - start) * 1000,
                "body": json.loads(body) if response.status in {200, 503} else {}}
    except (OSError, ValueError, http.client.HTTPException):
        return {"status": 0, "milliseconds": (time.perf_counter() - start) * 1000, "body": {}}
    finally:
        connection.close()


def recovery():
    parent = ROOT / ".local/recovery"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="synthetic-", dir=parent) as folder:
        root = Path(folder).resolve()
        if not root.is_relative_to(parent.resolve()):
            raise ValueError("Recovery directory escaped workspace")
        original, backup, restored = (root / name for name in ("original", "backup", "restored"))
        original.mkdir()
        (original / "cv.pdf").write_bytes(b"%PDF-synthetic recovery rehearsal")
        (original / "photo.png").write_bytes(b"synthetic photo")
        expected = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in original.iterdir()}
        shutil.copytree(original, backup)
        shutil.copytree(backup, restored)
        actual = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in restored.iterdir()}
        return {"passed": expected == actual, "files": len(expected), "scope": "Synthetic private files only; not a cloud restore"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["probe", "load", "recovery"])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--staging-host", help="Exact authorized staging hostname; production is not an implicit target")
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / ".local/operations-check.json")
    args = parser.parse_args()
    address = urlsplit(args.base_url)
    loopback = address.hostname in {"localhost", "127.0.0.1"}
    if address.scheme not in {"http", "https"} or address.username or address.password or address.path not in {"", "/"} or address.query or address.fragment or not (loopback or address.scheme == "https" and args.staging_host == address.hostname):
        parser.error("Usa loopback o el hostname HTTPS de staging expresamente autorizado")
    if not 1 <= args.requests <= 200 or not 1 <= args.workers <= 8:
        parser.error("Máximo 200 solicitudes y 8 conexiones")
    report = {"command": args.command, "generated_at": datetime.now(timezone.utc).isoformat(), "scope": "loopback" if loopback else "authorized_staging", "cloud_validated": False}
    if args.command == "recovery":
        report.update(recovery())
    elif args.command == "probe":
        live, ready = probe(args.base_url, "/health/live"), probe(args.base_url, "/health/ready")
        report.update(passed=live["status"] == ready["status"] == 200, live_status=live["status"], ready_status=ready["status"], checks=ready["body"].get("checks", {}))
    else:
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            values = list(pool.map(lambda _: probe(args.base_url, "/health/ready"), range(args.requests)))
        latency = sorted(row["milliseconds"] for row in values)
        failed = sum(row["status"] != 200 for row in values)
        p95 = latency[math.ceil(len(latency) * .95) - 1]
        report.update(passed=failed == 0 and p95 <= 2000, requests=len(values), workers=args.workers, failures=failed, p95_ms=round(p95, 2), elapsed_seconds=round(time.perf_counter() - started, 2), note="Solo readiness. No representa carga de extracción de CV, matching ni videollamadas.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Operaciones: {args.command}: {'aprobado' if report['passed'] else 'requiere revisión'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
