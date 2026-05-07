from fastapi import APIRouter, Depends
from app.database import get_db
from app.services import notification_service
from app.routers.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
def get_notifs(conn=Depends(get_db), user: dict = Depends(get_current_user)):
    return notification_service.get_my_notifications(conn, user["username"])

@router.patch("/{notification_id}/read")
def read_notif(notification_id: int, conn=Depends(get_db), user: dict = Depends(get_current_user)):
    return notification_service.mark_as_read(conn, user["username"], notification_id)