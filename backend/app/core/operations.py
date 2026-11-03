"""Bounded per-process diagnostics. No URLs with IDs, identities, bodies or credentials."""
from collections import OrderedDict, deque
from datetime import datetime
from math import ceil
from threading import Lock
from time import monotonic


class RequestMetrics:
    def __init__(self):
        self.rows = OrderedDict()
        self.lock = Lock()
        self.started = monotonic()

    def observe(self, method, route, status, milliseconds):
        key = (method, route)
        with self.lock:
            if key not in self.rows:
                if len(self.rows) >= 128:
                    self.rows.popitem(last=False)
                self.rows[key] = deque(maxlen=512)
            self.rows[key].append((monotonic(), milliseconds, status))

    def snapshot(self):
        cutoff, rows = monotonic() - 900, []
        with self.lock:
            for (method, route), values in self.rows.items():
                recent = [value for value in values if value[0] >= cutoff]
                if not recent:
                    continue
                latencies = sorted(value[1] for value in recent)
                errors = sum(value[2] >= 500 for value in recent)
                rows.append({"method": method, "route": route, "samples": len(recent), "errors": errors,
                             "p95_ms": round(latencies[max(0, ceil(len(latencies) * .95) - 1)], 1)})
        return {"window_minutes": 15, "sample_limit_per_route": 512, "uptime_seconds": round(monotonic() - self.started),
                "generated_at": datetime.utcnow().isoformat() + "Z", "routes": sorted(rows, key=lambda row: row["p95_ms"], reverse=True)}


metrics = RequestMetrics()
