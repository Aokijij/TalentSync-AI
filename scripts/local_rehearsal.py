"""Complete zero-budget local rehearsal with private-free reports."""
import json
import subprocess
import time

import local
from local_checks import save_report, source_fingerprint


def main():
    initial = source_fingerprint()
    report = {"passed": False, "source_sha256": initial, "steps": [],
              "scope": "local SQLite and owned loopback PostgreSQL; no deployment or external delivery"}
    env = local.prepare_environment()
    env["TALENTSYNC_LOCAL_REHEARSAL"] = "1"
    commands = [("complete_validation", "scripts/local.py", "verify"),
                ("postgres_recovery", "scripts/staging_postgres.py", "check"),
                ("local_doctor", "scripts/local.py", "doctor")]
    try:
        for name, script, command in commands:
            started = time.perf_counter()
            result = subprocess.run([str(local.PYTHON), script, command], cwd=local.ROOT, env=env, check=False)
            report["steps"].append({"name": name, "passed": result.returncode == 0,
                                    "seconds": round(time.perf_counter() - started, 2)})
            if result.returncode:
                break
        else:
            reports = [(local.LOCAL / "verification" / "validation.json", "source_sha256"),
                       (local.LOCAL / "staging" / "verification.json", "source_fingerprint")]
            report["passed"] = all(json.loads(path.read_text(encoding="utf-8")).get(key) == initial
                                   for path, key in reports) and source_fingerprint() == initial
            for name in ["capacity", "matching-regressions"]:
                path = local.LOCAL / "verification" / f"{name}.json"
                report["passed"] = report["passed"] and json.loads(path.read_text(encoding="utf-8")).get("passed") is True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report["error_type"] = type(error).__name__
    save_report("rehearsal", report)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
