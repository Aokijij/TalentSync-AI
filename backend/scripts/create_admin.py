import argparse
from getpass import getpass

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Profile, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.security.passwords import hash_password


class AdminInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)


def create_admin(db: Session, name: str, email: str, password: str) -> User:
    account = AdminInput(name=name, email=email, password=password)
    if len(account.password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar 72 bytes en UTF-8")
    if db.query(User).filter(User.email == account.email).first() is not None:
        raise ValueError("Ya existe una cuenta con ese correo; no se modificó su rol")
    user = User(
        name=account.name,
        email=str(account.email),
        password_hash=hash_password(account.password),
        role=UserRole.ADMIN,
    )
    user.profile = Profile()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear una cuenta administradora")
    parser.add_argument("--name", required=True, help="Nombre de la persona administradora")
    parser.add_argument("--email", required=True, help="Correo de acceso")
    arguments = parser.parse_args()
    password = getpass("Contraseña: ")
    if password != getpass("Repite la contraseña: "):
        parser.error("Las contraseñas no coinciden")
    try:
        with SessionLocal() as db:
            user = create_admin(db, arguments.name, arguments.email, password)
            print(f"Cuenta administradora creada: {user.email}")
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
