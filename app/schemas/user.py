from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.role import RoleEnum


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    roles: list[RoleEnum] = Field(default_factory=lambda: [RoleEnum.REPORTANTE])


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    roles: list[RoleEnum]
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    roles: Optional[list[RoleEnum]] = None
    is_active: Optional[bool] = None
