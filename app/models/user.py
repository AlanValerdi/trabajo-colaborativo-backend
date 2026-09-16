from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.role import RoleEnum
from app.models.user_role import UserRole

__all__ = ["RoleEnum", "User"]


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, index=True)
    password_hash: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user_roles: list[UserRole] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @property
    def roles(self) -> list[RoleEnum]:
        return [entry.role for entry in self.user_roles]

    def has_any_role(self, *roles: RoleEnum) -> bool:
        allowed = set(roles)
        return any(role in allowed for role in self.roles)
