import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def submit_complaint(conn, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO complaint (resident_id, complaint_title, complaint_description, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING complaint_id
        """, (resident_id, data.get("complaint_title"), data.get("complaint_description")))
        
        complaint_id = cursor.fetchone()["complaint_id"]
        conn.commit()
        return {"success": True, "complaint_id": complaint_id, "message": "Complaint filed"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Complaint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit complaint")

def get_my_complaints(conn, resident_id: int):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT complaint_id, complaint_title, complaint_description, status, created_at
        FROM complaint WHERE resident_id = %s ORDER BY created_at DESC
    """, (resident_id,))
    rows = cursor.fetchall()
    for r in rows:
        r["created_at"] = str(r["created_at"]) if r["created_at"] else None
    return rows