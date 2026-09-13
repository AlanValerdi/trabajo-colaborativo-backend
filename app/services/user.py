from sqlalchemy.orm import Session
from sqlmodel import select

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User)).all())


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
