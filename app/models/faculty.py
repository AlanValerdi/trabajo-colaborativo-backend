from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.location import Location


class Faculty(SQLModel, table=True):
    __tablename__ = "faculties"

    id: Optional[int] = Field(default=None, primary_key=True)
    campus_id: int = Field(foreign_key="campuses.id", nullable=False, index=True)
    name: str = Field(nullable=False, max_length=255)

    campus: "Campus" = Relationship(back_populates="faculties")
    locations: list[Location] = Relationship(back_populates="faculty")
