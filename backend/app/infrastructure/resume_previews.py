"""Short-lived, owner-scoped PDF previews; no CV copies are saved to disk."""
from collections import OrderedDict
from threading import Lock
from time import monotonic
from uuid import uuid4

from app.application.errors import UseCaseError


class ResumePreviews:
    def __init__(self):
        self.entries = OrderedDict()
        self.lock = Lock()

    def put(self, owner_id, content, filename):
        with self.lock:
            self._expire()
            # Bound total memory and retained previews per owner.
            own = [key for key, value in self.entries.items() if value[0] == owner_id]
            for key in own[:-2]:
                self.entries.pop(key)
            while self.entries and (len(self.entries) >= 64 or sum(len(value[1]) for value in self.entries.values()) + len(content) > 32_000_000):
                self.entries.popitem(last=False)
            if len(content) > 32_000_000:
                raise UseCaseError(status_code=422, detail="El documento es demasiado grande para la vista previa")
            token = uuid4().hex
            self.entries[token] = (owner_id, content, filename, monotonic() + 600)
            return token

    def _expire(self):
        for key, value in list(self.entries.items()):
            if value[3] <= monotonic():
                self.entries.pop(key)

    def get(self, owner_id, token, filename):
        with self.lock:
            self._expire()
            row = self.entries.get(token)
            if not row or row[0] != owner_id or row[2] != filename:
                raise UseCaseError(status_code=404, detail="La vista previa venció. Actualiza el documento para volver a abrirlo")
            return row[1]


resume_previews = ResumePreviews()
