from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlmodel import select

from app.core.security import hash_password
from app.models.role import RoleEnum
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate


def serialize_user(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        roles=user.roles,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def serialize_users(users: list[User]) -> list[UserRead]:
    return [serialize_user(user) for user in users]


def _assign_roles(db: Session, user: User, roles: list[RoleEnum]) -> None:
    unique_roles = list(dict.fromkeys(roles))
    if not unique_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario debe conservar al menos un rol",
        )

    user.user_roles.clear()
    for role in unique_roles:
        user.user_roles.append(UserRole(user_id=user.id, role=role))
    db.add(user)


def create_user(db: Session, user_in: UserCreate) -> UserRead:
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.flush()
    _assign_roles(db, user, user_in.roles)
    db.commit()
    db.refresh(user)
    user = get_user(db, user.id)
    assert user is not None
    return serialize_user(user)


def list_users(db: Session) -> list[UserRead]:
    users = list(
        db.scalars(select(User).options(selectinload(User.user_roles)).order_by(User.id)).all()
    )
    return serialize_users(users)


def get_user(db: Session, user_id: int) -> User | None:
    return db.scalar(
        select(User).options(selectinload(User.user_roles)).where(User.id == user_id)
    )


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> UserRead | None:
    user = get_user(db, user_id)
    if user is None:
        return None

    update_data = user_in.model_dump(exclude_unset=True)
    roles = update_data.pop("roles", None)

    for field, value in update_data.items():
        setattr(user, field, value)

    if roles is not None:
        _assign_roles(db, user, roles)

    db.commit()
    db.refresh(user)
    user = get_user(db, user_id)
    assert user is not None
    return serialize_user(user)
