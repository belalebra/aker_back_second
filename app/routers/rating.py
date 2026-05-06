from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.services import rating_service
from app.routers.dependencies import get_current_user, get_resident_id

router = APIRouter(prefix="/ratings", tags=["Ratings"])


# ── Schemas ───────────────────────────────────────────────────
class RatingCreate(BaseModel):
    booking_id: int
    rating: int          # 1 - 5
    review: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────
@router.post("/submit")
def submit_rating(
    data: RatingCreate,
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit a rating for a completed booking. Requires authentication."""
    resident_id = get_resident_id(conn, current_user["username"])
    return rating_service.submit_rating(conn, resident_id, data.model_dump())


@router.get("/employee/{employee_id}")
def get_employee_ratings(
    employee_id: int,
    conn=Depends(get_db)
):
    """Get all ratings for a specific employee. Public endpoint."""
    return rating_service.get_employee_ratings(conn, employee_id)
