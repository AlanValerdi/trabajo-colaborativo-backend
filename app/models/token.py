from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    token: str = Field(nullable=False, unique=True, max_length=512)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
