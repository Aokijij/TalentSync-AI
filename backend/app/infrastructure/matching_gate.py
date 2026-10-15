"""Coalesce overlapping batches without making request threads wait for inference."""
from contextlib import contextmanager
from threading import BoundedSemaphore, Lock

_guard = Lock()
_slots = {}
_capacity = BoundedSemaphore(2)


@contextmanager
def matching_slot(user_id):
    with _guard:
        slot = _slots.setdefault(user_id, {"lock": Lock(), "references": 0})
        slot["references"] += 1
    locked = slot["lock"].acquire(blocking=False)
    acquired = locked and _capacity.acquire(blocking=False)
    try:
        yield acquired
    finally:
        if acquired:
            _capacity.release()
        if locked:
            slot["lock"].release()
        with _guard:
            slot["references"] -= 1
            if not slot["references"]:
                _slots.pop(user_id, None)
