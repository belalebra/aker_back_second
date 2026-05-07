from fastapi import APIRouter, Depends
from typing import List
from app.database import get_db
from app.services import booking_service
from app.schemas.booking import ServiceOut, ProfessionalOut, BookingCreate
from app.routers.dependencies import get_current_user, get_resident_id

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("/services", response_model=List[ServiceOut])
def list_services(conn=Depends(get_db)):
    return booking_service.get_all_services(conn)

@router.get("/professionals/{category}", response_model=List[ProfessionalOut])
def list_pros(category: str, conn=Depends(get_db)):
    return booking_service.get_professionals_by_category(conn, category)

@router.post("/create")
def book(data: BookingCreate, conn=Depends(get_db), user: dict = Depends(get_current_user)):
    res_id = get_resident_id(conn, user["username"])
    return booking_service.create_booking(conn, res_id, data.model_dump())

@router.get("/my")
def my_history(conn=Depends(get_db), user: dict = Depends(get_current_user)):
    res_id = get_resident_id(conn, user["username"])
    return booking_service.get_my_bookings(conn, res_id)