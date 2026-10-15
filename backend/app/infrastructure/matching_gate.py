"""Coalesce overlapping batches without making request threads wait for inference."""
from contextlib import contextmanager
from threading import Lock

_guard = Lock()
_slots = {}


@contextmanager
def matching_slot(user_id):
    with _guard:
        slot = _slots.setdefault(user_id, {"lock": Lock(), "references": 0})
        slot["references"] += 1
    acquired = slot["lock"].acquire(blocking=False)
    try:
        yield acquired
    finally:
        if acquired:
            slot["lock"].release()
        with _guard:
            slot["references"] -= 1
            if not slot["references"]:
                _slots.pop(user_id, None)
