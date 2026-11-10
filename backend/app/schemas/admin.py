"""Schemas for the root admin's user, staff, invitation and activity management."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.auth import UserOut, clean_full_name
from app.schemas.content import InputModel, OutputModel
from app.schemas.student import ProfileOut


class AuditLogOut(OutputModel):
    id: int
    actor_id: int | None
    actor_name: str | None
    category: str
    action: str
    entity_type: str | None
    entity_id: int | None
    summary: str
    created_at: datetime


class UserListOut(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class UserUpdate(InputModel):
    full_name: str | None = None
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def check_name(cls, value):
        return clean_full_name(value) if value is not None else None


class UserDetailOut(UserOut):
    profile: ProfileOut | None = None
    permissions: dict[str, str] = {}
    recent_activity: list[AuditLogOut] = []


class StaffOut(UserOut):
    permissions: dict[str, str] = {}


class PermissionsUpdate(BaseModel):
    # {module: "read" | "write" | "read_write" | null}; null or missing removes access
    permissions: dict[str, str | None]


class InvitationCreate(InputModel):
    full_name: str
    email: EmailStr
    permissions: dict[str, str | None]

    @field_validator("full_name")
    @classmethod
    def check_name(cls, value):
        return clean_full_name(value)


class InvitationOut(OutputModel):
    id: int
    full_name: str
    email: str
    permissions: dict[str, str]
    status: str
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None
    invited_by_name: str | None = None


class OverviewOut(BaseModel):
    role: str
    stats: dict[str, int]
    permissions: dict[str, str]
    recent_accounts: list[UserOut] = []
    recent_content: list[AuditLogOut] = []
    recent_account_activity: list[AuditLogOut] = []
