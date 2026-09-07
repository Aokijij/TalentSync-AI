import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Base, User
from app.infrastructure.security.passwords import verify_password
from scripts.create_admin import create_admin


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_creates_admin_with_hashed_password_and_profile(db):
    password = "Testing-account-2026!"
    user = create_admin(db, "Administrador", "operator@example.com", password)
    assert user.role == UserRole.ADMIN
    assert user.password_hash != password
    assert verify_password(password, user.password_hash)
    assert user.profile.user_id == user.id


def test_existing_account_is_not_promoted_or_overwritten(db):
    existing = User(name="Candidato", email="person@example.com", password_hash="existing-hash", role=UserRole.CANDIDATE)
    db.add(existing)
    db.commit()
    with pytest.raises(ValueError, match="Ya existe"):
        create_admin(db, "Administrador", existing.email, "Testing-account-2026!")
    db.refresh(existing)
    assert existing.role == UserRole.CANDIDATE
    assert existing.password_hash == "existing-hash"
    assert db.query(User).count() == 1


def test_rejects_password_that_bcrypt_would_truncate(db):
    with pytest.raises(ValueError, match="72 bytes"):
        create_admin(db, "Administrador", "operator@example.com", "á" * 37)
    assert db.query(User).count() == 0
