from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.faculty import Faculty


class Campus(SQLModel, table=True):
    __tablename__ = "campuses"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(nullable=False, unique=True, index=True, max_length=32)
    name: str = Field(nullable=False, max_length=255)

    faculties: list[Faculty] = Relationship(back_populates="campus")
