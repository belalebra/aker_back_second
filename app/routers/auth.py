from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: EmailStr
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*)")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r"^01[0125]\d{8}$", v):
            raise ValueError("Invalid Egyptian phone number")
        return v


class TokenResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None


class ProfileResponse(BaseModel):
    username: str
    email: str
    role: str