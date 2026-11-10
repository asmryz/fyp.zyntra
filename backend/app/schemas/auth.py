from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 characters long.")
    if not any(ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        raise ValueError("Password must contain at least one letter and one number.")
    return password


def clean_full_name(value: str) -> str:
    value = " ".join(value.split())
    if len(value) < 2:
        raise ValueError("Please enter your full name.")
    if len(value) > 120:
        raise ValueError("Name must be at most 120 characters long.")
    return value


class NewPasswordMixin(BaseModel):
    password: str
    confirm_password: str

    @field_validator("password")
    @classmethod
    def check_strength(cls, value):
        return validate_password_strength(value)

    @model_validator(mode="after")
    def check_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class RegisterRequest(NewPasswordMixin):
    full_name: str
    email: EmailStr

    @field_validator("full_name")
    @classmethod
    def check_name(cls, value):
        return clean_full_name(value)


class EmailRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ResetPasswordRequest(NewPasswordMixin):
    reset_token: str


class AcceptInvitationRequest(NewPasswordMixin):
    token: str


class MessageResponse(BaseModel):
    message: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    last_login_at: datetime | None = None


class SessionUser(UserOut):
    # {module: access_level}; empty for students
    permissions: dict[str, str] = {}


def user_with_permissions(schema, user, permissions: dict):
    """
    Build a user response with a `permissions` dictionary.
    The User model also has a `permissions` attribute (a list of database
    rows), so the schema cannot read it directly from the model.
    """
    return schema(**UserOut.model_validate(user).model_dump(), permissions=permissions)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: SessionUser


class ResetTokenResponse(BaseModel):
    reset_token: str


class InvitationPreview(BaseModel):
    full_name: str
    email: str
    expires_at: datetime
    permissions: dict[str, str]
