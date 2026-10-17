from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.evidence import EvidenceStageEnum


class EvidenceUploader(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str


class EvidenceRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    report_id: int
    uploader_id: int
    uploader: EvidenceUploader
    file_url: str
    caption: Optional[str]
    stage: Optional[EvidenceStageEnum]
    created_at: datetime
