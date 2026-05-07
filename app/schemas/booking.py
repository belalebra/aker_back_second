from pydantic import BaseModel
from typing import Optional
from datetime import date


class ServiceOut(BaseModel):
    major_id: int
    major_name: str


class ProfessionalOut(BaseModel):
    employee_id: int
    f_name: str
    l_name: str
    job_type: str
    rating: Optional[float] = None
    home_service: Optional[bool] = None
    night_service: Optional[bool] = None
    is_emergency: Optional[bool] = None
    availability: Optional[bool] = None
    profile_image: Optional[str] = None
    employee_di: Optional[str] = None


class BookingCreate(BaseModel):
    employee_id: int
    service_type: str
    scheduled_date: Optional[date] = None
    is_emergency: Optional[bool] = False
    notes: Optional[str] = None
    payment_method_id: Optional[int] = None


class BookingOut(BaseModel):
    booking_id: int
    service_type: str
    status: Optional[str] = None


class UserProfileOut(BaseModel):
    username: str
    email: str
    role: str
    f_name: Optional[str] = None
    l_name: Optional[str] = None
    phone: Optional[str] = None
    area: Optional[str] = None
    apartment_number: Optional[int] = None
    unit_number: Optional[int] = None
    joining_date: Optional[str] = None
    total_requests: Optional[int] = None