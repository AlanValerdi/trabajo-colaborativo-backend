from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.models.role import RoleEnum


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    role: RoleEnum = Field(
        sa_column=Column(
            SAEnum(
                RoleEnum,
                values_callable=lambda obj: [e.value for e in obj],
            ),
            nullable=False,
            primary_key=True,
        ),
    )

    user: "User" = Relationship(back_populates="user_roles")
