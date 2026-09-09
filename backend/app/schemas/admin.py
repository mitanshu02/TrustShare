import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminUserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    account_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStatusUpdate(BaseModel):
    account_status: str = Field(pattern=r"^(active|inactive|locked)$")


class AdminFileOut(BaseModel):
    id: uuid.UUID
    original_name: str
    owner_email: str
    size_bytes: int
    created_at: datetime


class PlatformStatsOut(BaseModel):
    total_users: int
    total_files: int
    total_storage_bytes: int
    total_shares: int


class RoleChangeRequest(BaseModel):
    new_role: str = Field(pattern=r"^(admin|user)$")
    current_password: str = Field(min_length=1)


class RoleChangeAuditOut(BaseModel):
    id: uuid.UUID
    changed_by_email: str
    target_user_email: str
    old_role: str
    new_role: str
    created_at: datetime