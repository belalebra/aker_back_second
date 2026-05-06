import logging
from pyodbc import Connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Get My Notifications ──────────────────────────────────────
def get_my_notifications(conn: Connection, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                notification_id, title, message, is_read, created_at
            FROM Notifications
            WHERE username = ?
            ORDER BY created_at DESC
        """, username)
        rows = cursor.fetchall()
        return [
            {
                "notification_id": r.notification_id,
                "title":           r.title,
                "message":         r.message,
                "is_read":         bool(r.is_read),
                "created_at":      str(r.created_at) if r.created_at else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_notifications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


# ── Mark Notification as Read ─────────────────────────────────
def mark_as_read(conn: Connection, username: str, notification_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT notification_id FROM Notifications WHERE notification_id = ? AND username = ?",
            notification_id, username
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Notification not found or not yours")

        cursor.execute(
            "UPDATE Notifications SET is_read = 1 WHERE notification_id = ?",
            notification_id
        )
        conn.commit()

        logger.info(f"Notification {notification_id} marked as read by {username}")
        return {"success": True, "message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"mark_as_read error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


# ── Mark All as Read ──────────────────────────────────────────
def mark_all_as_read(conn: Connection, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Notifications SET is_read = 1 WHERE username = ?",
            username
        )
        conn.commit()

        logger.info(f"All notifications marked as read for {username}")
        return {"success": True, "message": "All notifications marked as read"}
    except Exception as e:
        logger.error(f"mark_all_as_read error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notifications")


# ── Send Notification (Admin) ─────────────────────────────────
def send_notification(conn: Connection, username: str, title: str, message: str):
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT username FROM Login WHERE username = ?", username)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("""
            INSERT INTO Notifications (username, title, message, is_read)
            VALUES (?, ?, ?, 0)
        """, username, title, message)
        conn.commit()

        logger.info(f"Notification sent to {username}")
        return {"success": True, "message": "Notification sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"send_notification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


# ── Get Unread Count ──────────────────────────────────────────
def get_unread_count(conn: Connection, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS unread FROM Notifications WHERE username = ? AND is_read = 0",
            username
        )
        row = cursor.fetchone()
        return {"unread_count": row.unread}
    except Exception as e:
        logger.error(f"get_unread_count error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unread count")
