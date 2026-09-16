"""Persistent image storage: private Azure blobs in production, local files in development."""
from functools import lru_cache
from pathlib import Path

from app.application.errors import UseCaseError
from app.core.config import settings


@lru_cache(maxsize=4)
def blob_container(account_url: str, container_name: str):
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
    return service.get_container_client(container_name)


class ImageStorage:
    def __init__(self, upload_dir: str, account_url: str | None, container_name: str):
        self.upload_dir = Path(upload_dir)
        self.account_url = account_url
        self.container_name = container_name

    def save(self, folder: str, filename: str, content: bytes, media_type: str) -> None:
        if self.account_url:
            from azure.storage.blob import ContentSettings

            try:
                blob_container(self.account_url, self.container_name).upload_blob(
                    name=f"{folder}/{Path(filename).name}", data=content, overwrite=False,
                    content_settings=ContentSettings(content_type=media_type),
                )
            except Exception as exc:
                raise UseCaseError(status_code=503, detail="No fue posible guardar la imagen. Inténtalo de nuevo.") from exc
        else:
            try:
                directory = self.upload_dir / folder
                directory.mkdir(parents=True, exist_ok=True)
                (directory / Path(filename).name).write_bytes(content)
            except OSError as exc:
                raise UseCaseError(status_code=503, detail="No fue posible guardar la imagen. Inténtalo de nuevo.") from exc

    def read(self, folder: str, filename: str) -> bytes:
        if self.account_url:
            from azure.core.exceptions import ResourceNotFoundError

            try:
                return blob_container(self.account_url, self.container_name).download_blob(
                    f"{folder}/{Path(filename).name}"
                ).readall()
            except ResourceNotFoundError as exc:
                raise UseCaseError(status_code=404, detail="Imagen no encontrada") from exc
            except Exception as exc:
                raise UseCaseError(status_code=503, detail="No fue posible cargar la imagen. Inténtalo de nuevo.") from exc
        try:
            return (self.upload_dir / folder / Path(filename).name).read_bytes()
        except FileNotFoundError as exc:
            raise UseCaseError(status_code=404, detail="Imagen no encontrada") from exc
        except OSError as exc:
            raise UseCaseError(status_code=503, detail="No fue posible cargar la imagen. Inténtalo de nuevo.") from exc


def get_image_storage() -> ImageStorage:
    return ImageStorage(settings.upload_dir, settings.azure_storage_account_url, settings.azure_storage_container)
