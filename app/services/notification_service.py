import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def get_my_notifications(conn, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT notification_id, title, message, is_read, created_at
            FROM notifications WHERE username = %s ORDER BY created_at DESC
        """, (username,))
        rows = cursor.fetchall()
        return [
            {
                "notification_id": r[0], "title": r[1], "message": r[2],
                "is_read": bool(r[3]), "created_at": str(r[4]) if r[4] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_notifications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


def mark_as_read(conn, username: str, notification_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT notification_id FROM notifications WHERE notification_id = %s AND username = %s", (notification_id, username))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Notification not found or not yours")
        cursor.execute("UPDATE notifications SET is_read = true WHERE notification_id = %s", (notification_id,))
        conn.commit()
        return {"success": True, "message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"mark_as_read error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


def mark_all_as_read(conn, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = true WHERE username = %s", (username,))
        conn.commit()
        return {"success": True, "message": "All notifications marked as read"}
    except Exception as e:
        logger.error(f"mark_all_as_read error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notifications")


def send_notification(conn, username: str, title: str, message: str):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM login WHERE username = %s", (username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        cursor.execute("INSERT INTO notifications (username, title, message, is_read) VALUES (%s, %s, %s, false)", (username, title, message))
        conn.commit()
        return {"success": True, "message": "Notification sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"send_notification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


def get_unread_count(conn, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE username = %s AND is_read = false", (username,))
        row = cursor.fetchone()
        return {"unread_count": row[0]}
    except Exception as e:
        logger.error(f"get_unread_count error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch unread count")