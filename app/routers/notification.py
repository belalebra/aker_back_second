from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import get_db
from app.services import notification_service
from app.routers.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ── Schemas ───────────────────────────────────────────────────
class SendNotificationRequest(BaseModel):
    username: str
    title:    str
    message:  str


# ── GET /notifications ────────────────────────────────────────
@router.get("")
def get_notifications(
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all notifications for the logged-in user."""
    return notification_service.get_my_notifications(conn, current_user["username"])


# ── GET /notifications/unread-count ──────────────────────────
@router.get("/unread-count")
def unread_count(
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get count of unread notifications."""
    return notification_service.get_unread_count(conn, current_user["username"])


# ── PATCH /notifications/{id} ────────────────────────────────
@router.patch("/{notification_id}")
def mark_as_read(
    notification_id: int,
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read."""
    return notification_service.mark_as_read(conn, current_user["username"], notification_id)


# ── PATCH /notifications/read-all ────────────────────────────
@router.patch("/read-all/mark")
def mark_all_as_read(
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read."""
    return notification_service.mark_all_as_read(conn, current_user["username"])


# ── POST /notifications/send (Admin) ─────────────────────────
@router.post("/send")
def send_notification(
    data: SendNotificationRequest,
    conn=Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Send a notification to a user. Admin only."""
    return notification_service.send_notification(conn, data.username, data.title, data.message)
