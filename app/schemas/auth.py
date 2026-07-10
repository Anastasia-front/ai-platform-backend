import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.core import PASSWORD_RULE_MESSAGE


def validate_secure_password(password: str) -> str:
    if (
        len(password) < 6
        or not re.search(r"[A-Z]", password)
        or not re.search(r"\d", password)
        or not re.search(r"[^A-Za-z0-9]", password)
    ):
        raise ValueError(PASSWORD_RULE_MESSAGE)

    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_is_secure(cls, password: str) -> str:
        return validate_secure_password(password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    refresh_expires_in: int | None = None
