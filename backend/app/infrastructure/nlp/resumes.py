from pathlib import Path

from app.application.errors import UseCaseError
from app.application.ports.services import UploadedResume
from app.core.config import settings
from app.infrastructure.nlp.pdf_reader import extract_pdf_text

MAX_CV_BYTES = 5 * 1024 * 1024


class ResumeReader:
    def storage_available(self) -> bool:
        directory = Path(settings.upload_dir)
        return directory.exists() and directory.is_dir()

    def extract(self, file: UploadedResume, user_id: int) -> tuple[str, str]:
        filename = file.filename or ""
        is_pdf = file.content_type in {
            "application/pdf",
            "application/x-pdf",
            "application/octet-stream",
        } and filename.lower().endswith(".pdf")
        if not is_pdf:
            raise UseCaseError(status_code=400, detail="Solo se permiten archivos PDF")
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename or "cv.pdf").name.replace(" ", "_")
        file_path = upload_dir / f"user_{user_id}_{safe_name}"
        content = file.file.read()
        if not content:
            raise UseCaseError(status_code=400, detail="El archivo PDF esta vacio")
        if len(content) > MAX_CV_BYTES:
            raise UseCaseError(status_code=400, detail="El PDF no puede superar 5 MB")
        file_path.write_bytes(content)
        try:
            raw_text = extract_pdf_text(str(file_path))
        except Exception as exc:
            raise UseCaseError(
                status_code=400, detail="No fue posible leer el PDF"
            ) from exc
        if not raw_text:
            raise UseCaseError(
                status_code=400,
                detail="El PDF no contiene texto extraíble (probablemente es un escaneo o una imagen). Usa un PDF exportado con texto seleccionable o una versión con OCR.",
            )
        return (safe_name, raw_text)
