from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="reports.id", nullable=False, index=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    content: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )