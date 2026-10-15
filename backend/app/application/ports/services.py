from typing import BinaryIO, Protocol

from app.domain.entities.catalog import CatalogPage
from app.domain.entities.nlp import NLPResult


class TextAnalysis(Protocol):
    def extract_skills(self, text: str) -> list[str]: ...
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
    def encrypt_secret(self, value: str) -> str: ...
    def decrypt_secret(self, value: str) -> str: ...


class MailDelivery(Protocol):
    def send(self, *, recipient: str, subject: str, body: str, message_id: int) -> None: ...


class MailDeliveryError(Exception):
    def __init__(self, *, retryable: bool, kind: str):
        super().__init__("Mail delivery unavailable")
        self.retryable = retryable
        self.kind = kind if kind in {"temporary", "permanent", "configuration", "transport"} else "transport"


class SocialIdentityProvider(Protocol):
    def configured(self, provider: str) -> bool: ...
    def authorization_url(self, provider: str, state: str, challenge: str, nonce: str) -> str: ...
    def exchange(self, provider: str, code: str, verifier: str, nonce: str) -> dict: ...


class UploadedResume(Protocol):
    filename: str | None
    content_type: str | None
    file: BinaryIO


class ProjectInspector(Protocol):
    def inspect(self, file: UploadedResume) -> dict: ...


class RepositoryInspector(Protocol):
    def inspect(self, url: str) -> dict: ...


class SQLPractice(Protocol):
    def run(self, query: str, dataset: dict) -> dict: ...


class CareerTextWriter(Protocol):
    def generate(self, record: dict, *, style: str, result: str) -> dict: ...


class InterviewConnectivity(Protocol):
    def configuration(self, room_id: str, user_id: int) -> dict: ...


class ResumeReader(Protocol):
    def original(self, profile) -> bytes: ...
    def extract(self, file: UploadedResume, user_id: int) -> tuple[str, str]: ...
    def storage_available(self) -> bool: ...


class ImageStorage(Protocol):
    def save(self, folder: str, filename: str, content: bytes, media_type: str) -> None: ...
    def read(self, folder: str, filename: str) -> bytes: ...


class JobCatalog(Protocol):
    @property
    def source_name(self) -> str: ...

    @property
    def registration_url(self) -> str: ...

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
