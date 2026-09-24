from typing import BinaryIO, Protocol

from app.domain.entities.catalog import CatalogPage
from app.domain.entities.nlp import NLPResult


class TextAnalysis(Protocol):
    def embed(self, text: str) -> list[float]: ...
    def analyze_cv(self, text: str) -> NLPResult: ...
    def analyze_job(self, text: str) -> NLPResult: ...
    def similarity_percentage(
        self, left: list[float] | None, right: list[float] | None
    ) -> float: ...


class AccountSecurity(Protocol):
    def hash_password(self, password: str) -> str: ...
    def verify_password(self, password: str, hashed: str) -> bool: ...
    def create_access_token(self, subject: str, role: str) -> str: ...


class UploadedResume(Protocol):
    filename: str | None
    content_type: str | None
    file: BinaryIO


class ResumeReader(Protocol):
    def extract(self, file: UploadedResume, user_id: int) -> tuple[str, str]: ...
    def storage_available(self) -> bool: ...


class ImageStorage(Protocol):
    def save(self, folder: str, filename: str, content: bytes, media_type: str) -> None: ...
    def read(self, folder: str, filename: str) -> bytes: ...


class JobCatalog(Protocol):
    @property
    def configured(self) -> bool: ...

    def search(
        self,
        *,
        keywords: str,
        location: str,
        page: int,
        result_count: int,
    ) -> CatalogPage: ...
