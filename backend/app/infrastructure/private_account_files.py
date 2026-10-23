"""Operate only on files with the platform's exact owner prefix, never whole directories."""
from pathlib import Path

from app.core.config import settings
from app.infrastructure.images import blob_container
from app.infrastructure.resume_previews import resume_previews

MAX_EXPORT = 50 * 1024 * 1024


class PrivateAccountFiles:
    def __init__(self, config=settings):
        self.config = config

    def _local(self, user_id):
        root = Path(self.config.upload_dir).resolve()
        for directory in (root, root / "profile_photos"):
            if not directory.exists():
                continue
            if directory.is_symlink() or not directory.resolve().is_relative_to(root):
                raise OSError("Unsafe private storage")
            for path in directory.glob(f"user_{int(user_id)}_*"):
                if path.is_symlink() or not path.resolve().is_relative_to(root):
                    raise OSError("Unsafe private file")
                if path.is_file():
                    yield path

    def _cloud(self, user_id):
        container = blob_container(self.config.azure_storage_account_url, self.config.azure_storage_container)
        count = 0
        for prefix in (f"users/{int(user_id)}/", f"profile_photos/user_{int(user_id)}_"):
            for row in container.list_blobs(name_starts_with=prefix):
                count += 1
                if count > 1000:
                    raise OSError("Private file count limit")
                yield container, row

    @staticmethod
    def _suffix(name):
        suffix = Path(name).suffix.lower()
        return suffix if suffix in {".pdf", ".png", ".jpg", ".jpeg", ".webp"} else ".bin"

    def export(self, user_id):
        files, size = [], 0
        if self.config.azure_storage_account_url:
            for container, row in self._cloud(user_id):
                size += row.size
                if size > MAX_EXPORT:
                    raise OSError("Export size limit")
                data = container.download_blob(row.name).readall()
                if len(data) != row.size:
                    raise OSError("Private file changed")
                files.append((f"files/{len(files) + 1}{self._suffix(row.name)}", data))
        else:
            for path in self._local(user_id):
                size += path.stat().st_size
                if size > MAX_EXPORT:
                    raise OSError("Export size limit")
                data = path.read_bytes()
                if len(data) > MAX_EXPORT or sum(len(value) for _, value in files) + len(data) > MAX_EXPORT:
                    raise OSError("Export size limit")
                files.append((f"files/{len(files) + 1}{self._suffix(path.name)}", data))
        return files

    def erase(self, user_id):
        resume_previews.forget_owner(user_id)
        if self.config.azure_storage_account_url:
            for container, row in self._cloud(user_id):
                container.delete_blob(row.name, delete_snapshots="include")
        else:
            for path in self._local(user_id):
                path.unlink(missing_ok=True)
