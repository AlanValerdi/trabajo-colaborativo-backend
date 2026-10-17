from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CommentCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    content: str = Field(min_length=1)
    mentions: Optional[list[int]] = Field(
        default=None,
        description="IDs de usuarios mencionados en el comentario (HU-14)",
    )


class CommentUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    content: str = Field(min_length=1)


class CommentAuthor(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str


class CommentMentionRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    name: str


class CommentRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    report_id: int
    user_id: int
    author: CommentAuthor
    content: str
    mentions: list[CommentMentionRead]
    created_at: datetime
