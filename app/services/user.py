from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(name=user_in.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User)).all())


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
