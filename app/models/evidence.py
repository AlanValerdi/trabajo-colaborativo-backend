from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class EvidenceStageEnum(str, Enum):
    ANTES = "antes"
    DURANTE = "durante"
    DESPUES = "despues"


class ReportEvidence(SQLModel, table=True):
    __tablename__ = "report_evidences"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="reports.id", nullable=False, index=True)
    uploader_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    file_url: str = Field(nullable=False, max_length=1024)
    caption: Optional[str] = Field(default=None, max_length=500)
    stage: Optional[EvidenceStageEnum] = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                EvidenceStageEnum,
                values_callable=lambda obj: [e.value for e in obj],
                name="evidencestageenum",
            ),
            nullable=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
