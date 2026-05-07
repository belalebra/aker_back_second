from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.services import rating_service
from app.routers.dependencies import get_current_user, get_resident_id

router = APIRouter(prefix="/ratings", tags=["Ratings"])


class RatingCreate(BaseModel):
    booking_id: int
    rating: int
    review: Optional[str] = None


@router.post("/submit")
def submit_rating(data: RatingCreate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    resident_id = get_resident_id(conn, current_user["username"])
    return rating_service.submit_rating(conn, resident_id, data.model_dump())


@router.get("/employee/{employee_id}")
def get_employee_ratings(employee_id: int, conn=Depends(get_db)):
    return rating_service.get_employee_ratings(conn, employee_id)