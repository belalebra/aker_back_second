from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.services import booking_service
from app.services.auth_service import get_user_by_username
from app.schemas.booking import ServiceOut, ProfessionalOut, BookingCreate, BookingOut, UserProfileOut
from app.routers.dependencies import get_current_user, get_current_admin, get_resident_id

router = APIRouter(tags=["AKAR Services"])


class BookingStatusUpdate(BaseModel):
    status: str

class ServiceCreate(BaseModel):
    major_name: str

class ServiceUpdate(BaseModel):
    major_name: str


@router.get("/services/all", response_model=List[ServiceOut])
def get_all_services(conn=Depends(get_db)):
    return booking_service.get_all_services(conn)


@router.get("/services/{service_id}")
def get_service(service_id: int, conn=Depends(get_db)):
    return booking_service.get_service_by_id(conn, service_id)


@router.post("/services")
def add_service(data: ServiceCreate, conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return booking_service.add_service(conn, data.major_name)


@router.put("/services/{service_id}")
def update_service(service_id: int, data: ServiceUpdate, conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return booking_service.update_service(conn, service_id, data.major_name)


@router.delete("/services/{service_id}")
def delete_service(service_id: int, conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return booking_service.delete_service(conn, service_id)


@router.get("/professionals/{category}", response_model=List[ProfessionalOut])
def get_professionals(category: str, conn=Depends(get_db)):
    return booking_service.get_professionals_by_category(conn, category)


@router.post("/bookings/create")
def create_booking(data: BookingCreate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    username = current_user.get("username")
    user = get_user_by_username(conn, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor = conn.cursor()
    cursor.execute("SELECT resident_id FROM resident WHERE email = %s", (user[4],))
    resident = cursor.fetchone()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    return booking_service.create_booking(conn, resident[0], data.model_dump())


@router.get("/bookings/my")
def my_bookings(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    resident_id = get_resident_id(conn, current_user["username"])
    return booking_service.get_my_bookings(conn, resident_id)


@router.get("/bookings/all")
def all_bookings(conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return booking_service.get_all_bookings(conn)


@router.patch("/bookings/{booking_id}/status")
def update_booking_status(booking_id: int, data: BookingStatusUpdate, conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return booking_service.update_booking_status(conn, booking_id, data.status)


@router.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    resident_id = get_resident_id(conn, current_user["username"])
    return booking_service.cancel_booking(conn, resident_id, booking_id)


@router.get("/user/profile", response_model=UserProfileOut)
def get_profile(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    return booking_service.get_user_profile(conn, current_user.get("username"))