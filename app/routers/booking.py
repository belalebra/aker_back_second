from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.services import booking_service
from app.services.auth_service import get_user_by_username
from app.schemas.booking import (
    ServiceOut, ProfessionalOut, BookingCreate, BookingOut, UserProfileOut
)
from app.routers.dependencies import get_current_user, get_current_admin, get_resident_id

router = APIRouter(tags=["AKAR Services"])


# ── Schemas ───────────────────────────────────────────────────
class BookingStatusUpdate(BaseModel):
    status: str  # pending | confirmed | in_progress | completed | cancelled

class ServiceCreate(BaseModel):
    major_name: str

class ServiceUpdate(BaseModel):
    major_name: str


# ── GET /services/all ─────────────────────────────────────────
@router.get("/services/all", response_model=List[ServiceOut])
def get_all_services(conn=Depends(get_db)):
    """Get all available service categories."""
    return booking_service.get_all_services(conn)


# ── GET /services/{service_id} ────────────────────────────────
@router.get("/services/{service_id}")
def get_service(service_id: int, conn=Depends(get_db)):
    """Get a specific service by ID."""
    return booking_service.get_service_by_id(conn, service_id)


# ── POST /services (Admin) ────────────────────────────────────
@router.post("/services")
def add_service(
    data: ServiceCreate,
    conn=Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Add a new service category. Admin only."""
    return booking_service.add_service(conn, data.major_name)


# ── PUT /services/{service_id} (Admin) ───────────────────────
@router.put("/services/{service_id}")
def update_service(
    service_id: int,
    data: ServiceUpdate,
    conn=Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Update a service category. Admin only."""
    return booking_service.update_service(conn, service_id, data.major_name)


# ── DELETE /services/{service_id} (Admin) ────────────────────
@router.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    conn=Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Delete a service category. Admin only."""
    return booking_service.delete_service(conn, service_id)


# ── GET /professionals/{category} ────────────────────────────
@router.get("/professionals/{category}", response_model=List[ProfessionalOut])
def get_professionals(category: str, conn=Depends(get_db)):
    """Get professionals by category. Examples: plumber, electrician, painter"""
    return booking_service.get_professionals_by_category(conn, category)


# ── POST /bookings/create ─────────────────────────────────────
@router.post("/bookings/create")
def create_booking(
    data: BookingCreate,
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new booking. Requires authentication."""
    username = current_user.get("username")
    user = get_user_by_username(conn, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor = conn.cursor()
    cursor.execute("SELECT resident_id FROM Resident WHERE email = ?", user.email)
    resident = cursor.fetchone()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident profile not found")

    return booking_service.create_booking(conn, resident.resident_id, data.model_dump())


# ── GET /bookings/my ──────────────────────────────────────────
@router.get("/bookings/my")
def my_bookings(
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all bookings for the logged-in resident."""
    resident_id = get_resident_id(conn, current_user["username"])
    return booking_service.get_my_bookings(conn, resident_id)


# ── GET /bookings/all (Admin) ─────────────────────────────────
@router.get("/bookings/all")
def all_bookings(
    conn=Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Get all bookings. Admin only."""
    return booking_service.get_all_bookings(conn)


# ── PATCH /bookings/{booking_id}/status (Admin) ───────────────
@router.patch("/bookings/{booking_id}/status")
def update_booking_status(
    booking_id: int,
    data: BookingStatusUpdate,
    conn=Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Update booking status. Admin only."""
    return booking_service.update_booking_status(conn, booking_id, data.status)


# ── DELETE /bookings/{booking_id} ─────────────────────────────
@router.delete("/bookings/{booking_id}")
def cancel_booking(
    booking_id: int,
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel a booking. Resident can only cancel their own bookings."""
    resident_id = get_resident_id(conn, current_user["username"])
    return booking_service.cancel_booking(conn, resident_id, booking_id)


# ── GET /user/profile ─────────────────────────────────────────
@router.get("/user/profile", response_model=UserProfileOut)
def get_profile(
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's full profile. Requires authentication."""
    username = current_user.get("username")
    return booking_service.get_user_profile(conn, username)
