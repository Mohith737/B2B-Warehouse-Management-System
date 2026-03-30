# /home/mohith/Catchup-Mohith/backend/app/schemas/user.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole
    is_active: bool = True


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


class UserListParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)
    role: UserRole | None = None
    is_active: bool | None = None
    search: str | None = None
