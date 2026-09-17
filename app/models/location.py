from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    faculty_id: int = Field(foreign_key="faculties.id", nullable=False, index=True)
    name: str = Field(nullable=False, max_length=255)

    faculty: "Faculty" = Relationship(back_populates="locations")
