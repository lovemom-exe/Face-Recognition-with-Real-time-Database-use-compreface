from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from .user import UserOut


class LoginRequest(BaseModel):
    username: str
    password: str


class TeacherRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8)


class TeacherRegisterResponse(BaseModel):
    message: str
    status: str
    user: UserOut


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
