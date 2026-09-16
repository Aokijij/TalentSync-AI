from pathlib import Path
from tempfile import NamedTemporaryFile

from app.application.errors import UseCaseError
from app.application.ports.services import UploadedResume
from app.core.config import settings
from app.infrastructure.nlp.pdf_reader import extract_pdf_text

MAX_CV_BYTES = 5 * 1024 * 1024


class ResumeReader:
    def storage_available(self) -> bool:
        if settings.azure_storage_account_url:
            try:
                return self._blob_container().exists()
            except Exception:
                return False
        directory = Path(settings.upload_dir)
        return directory.exists() and directory.is_dir()

    @staticmethod
    def _blob_container():
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        service = BlobServiceClient(
            account_url=settings.azure_storage_account_url,
            credential=DefaultAzureCredential(),
        )
        return service.get_container_client(settings.azure_storage_container)

    def extract(self, file: UploadedResume, user_id: int) -> tuple[str, str]:
        filename = file.filename or ""
        is_pdf = file.content_type in {
            "application/pdf",
            "application/x-pdf",
            "application/octet-stream",
        } and filename.lower().endswith(".pdf")
        if not is_pdf:
            raise UseCaseError(status_code=400, detail="Solo se permiten archivos PDF")
        safe_name = Path(filename or "cv.pdf").name.replace(" ", "_")
        content = file.file.read()
        if not content:
            raise UseCaseError(status_code=400, detail="El archivo PDF esta vacio")
        if len(content) > MAX_CV_BYTES:
            raise UseCaseError(status_code=400, detail="El PDF no puede superar 5 MB")
        temporary_path: Path | None = None
        if settings.azure_storage_account_url:
            with NamedTemporaryFile(suffix=".pdf", delete=False) as temporary_file:
                temporary_file.write(content)
                file_path = Path(temporary_file.name)
                temporary_path = file_path
        else:
            upload_dir = Path(settings.upload_dir)
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / f"user_{user_id}_{safe_name}"
            file_path.write_bytes(content)
        try:
            raw_text = extract_pdf_text(str(file_path))
        except Exception as exc:
            raise UseCaseError(
                status_code=400, detail="No fue posible leer el PDF"
            ) from exc
        finally:
            if temporary_path:
                temporary_path.unlink(missing_ok=True)
        if not raw_text:
            raise UseCaseError(
                status_code=400,
                detail="El PDF no contiene texto extraíble (probablemente es un escaneo o una imagen). Usa un PDF exportado con texto seleccionable o una versión con OCR.",
            )
        if settings.azure_storage_account_url:
            try:
                from azure.storage.blob import ContentSettings

                self._blob_container().upload_blob(
                    name=f"users/{user_id}/cv.pdf",
                    data=content,
                    overwrite=True,
                    content_settings=ContentSettings(content_type="application/pdf"),
                    metadata={"original_filename": safe_name},
                )
            except Exception as exc:
                raise UseCaseError(
                    status_code=503,
                    detail="No fue posible guardar el PDF en el almacenamiento",
                ) from exc
        return (safe_name, raw_text)
