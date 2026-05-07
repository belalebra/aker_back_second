from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import get_db
from app.services.complaint_service import (
    submit_complaint,
    get_my_complaints,
    get_all_complaints,
    update_complaint_status
)

from app.routers.dependencies import get_current_user, get_current_admin, get_resident_id

router = APIRouter(prefix="/complaints", tags=["Complaints"])


class ComplaintCreate(BaseModel):
    complaint_title: str
    complaint_description: str

class StatusUpdate(BaseModel):
    status: str


@router.post("/submit")
def submit_complaint(data: ComplaintCreate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    resident_id = get_resident_id(conn, current_user["username"])
    return complaint_service.submit_complaint(conn, resident_id, data.model_dump())


@router.get("/my")
def my_complaints(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    resident_id = get_resident_id(conn, current_user["username"])
    return complaint_service.get_my_complaints(conn, resident_id)


@router.get("/all")
def all_complaints(conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return complaint_service.get_all_complaints(conn)


@router.patch("/{complaint_id}/status")
def update_status(complaint_id: int, data: StatusUpdate, conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return complaint_service.update_complaint_status(conn, complaint_id, data.status)