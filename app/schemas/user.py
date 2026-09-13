from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import RoleEnum


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.REPORTANTE


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: RoleEnum
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None
