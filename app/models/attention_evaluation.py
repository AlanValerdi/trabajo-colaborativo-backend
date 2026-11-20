from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


class AttentionEvaluation(SQLModel, table=True):
    __tablename__ = 'attention_evaluations'
    __table_args__ = (
        UniqueConstraint('report_id', name='uq_attention_evaluation_report'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_attention_rating'),
    )

    id: int | None = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key='reports.id', nullable=False)
    author_id: int = Field(foreign_key='users.id', nullable=False)
    rating: int = Field(nullable=False)
    comment: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
