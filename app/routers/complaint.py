from fastapi import APIRouter, Depends
from app.database import get_db
from app.services import complaint_service
from app.routers.dependencies import get_current_user, get_resident_id

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.post("/submit")
def submit(data: dict, conn=Depends(get_db), user: dict = Depends(get_current_user)):
    res_id = get_resident_id(conn, user["username"])
    return complaint_service.submit_complaint(conn, res_id, data)

@router.get("/my")
def list_mine(conn=Depends(get_db), user: dict = Depends(get_current_user)):
    res_id = get_resident_id(conn, user["username"])
    return complaint_service.get_my_complaints(conn, res_id)