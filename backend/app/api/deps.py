from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.ports.services import AccountSecurity as AccountSecurityPort
from app.application.ports.services import ResumeReader as ResumeReaderPort
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.resumes import ResumeReader
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.accounts import AccountSecurity
from app.infrastructure.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token)
    if payload is None or payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        )
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no existe"
        )
    return user


def require_roles(*roles: UserRole):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado"
            )
        return current_user

    return checker


def get_unit_of_work(db: Session = Depends(get_db)) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(db)


def get_text_analysis() -> TextAnalysis:
    return text_processor


def get_account_security() -> AccountSecurityPort:
    return AccountSecurity()


def get_resume_reader() -> ResumeReaderPort:
    return ResumeReader()
