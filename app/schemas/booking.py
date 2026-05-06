import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ── Validators ────────────────────────────────────────────────
def validate_egyptian_phone(v: str) -> str:
    pattern = r'^(010|011|012|015)\d{8}$'
    if not re.match(pattern, v):
        raise ValueError('Phone must be a valid Egyptian number (e.g. 01012345678)')
    return v


# ── Service Schemas ───────────────────────────────────────────
class ServiceOut(BaseModel):
    major_id:   int
    major_name: str


# ── Professional Schemas ──────────────────────────────────────
class ProfessionalOut(BaseModel):
    employee_id:   int
    f_name:        str
    l_name:        str
    job_type:      str
    rating:        Optional[int]
    home_service:  Optional[str]
    night_service: Optional[str]
    is_emergency:  bool
    availability:  bool
    profile_image: Optional[str]
    employee_di:   Optional[str]


# ── Booking Schemas ───────────────────────────────────────────
class BookingCreate(BaseModel):
    employee_id:       int
    service_type:      str
    scheduled_date:    Optional[datetime] = None
    is_emergency:      bool = False
    notes:             Optional[str] = None
    payment_method_id: Optional[int] = None

    @field_validator('service_type')
    @classmethod
    def service_not_empty(cls, v):
        if not v.strip():
            raise ValueError('service_type cannot be empty')
        return v


class BookingOut(BaseModel):
    booking_id:     int
    service_type:   str
    status:         str
    is_emergency:   bool
    booking_date:   datetime
    scheduled_date: Optional[datetime]
    total_price:    Optional[float]
    notes:          Optional[str]


# ── Profile Schemas ───────────────────────────────────────────
class UserProfileOut(BaseModel):
    username:        str
    email:           str
    role:            str
    f_name:          Optional[str]
    l_name:          Optional[str]
    phone:           Optional[str]
    area:            Optional[str]
    apartment_number:Optional[str]
    unit_number:     Optional[str]
    joining_date:    Optional[str]
    total_requests:  Optional[int]


# ── Login / Register ──────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email:    EmailStr
    phone:    str

    @field_validator('phone')
    @classmethod
    def phone_valid(cls, v):
        return validate_egyptian_phone(v)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
