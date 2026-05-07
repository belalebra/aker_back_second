import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def submit_complaint(conn, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT resident_id FROM resident WHERE resident_id = %s", (resident_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Resident not found")
        cursor.execute("""
            INSERT INTO complaint (resident_id, complaint_title, complaint_description, status)
            VALUES (%s, %s, %s, 'pending')
        """, (resident_id, data["complaint_title"], data["complaint_description"]))
        conn.commit()
        cursor.execute("SELECT complaint_id FROM complaint WHERE resident_id = %s ORDER BY complaint_id DESC LIMIT 1", (resident_id,))
        new_complaint = cursor.fetchone()
        return {"success": True, "message": "Complaint submitted successfully", "complaint_id": new_complaint[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"submit_complaint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit complaint")


def get_my_complaints(conn, resident_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT complaint_id, complaint_title, complaint_description, status, created_at
            FROM complaint WHERE resident_id = %s ORDER BY complaint_id DESC
        """, (resident_id,))
        rows = cursor.fetchall()
        return [
            {
                "complaint_id": r[0], "complaint_title": r[1],
                "complaint_description": r[2], "status": r[3],
                "created_at": str(r[4]) if r[4] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_complaints error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch complaints")


def get_all_complaints(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.complaint_id, c.complaint_title, c.complaint_description,
                   c.status, c.created_at, r.f_name, r.l_name, r.apartment_number
            FROM complaint c
            LEFT JOIN resident r ON r.resident_id = c.resident_id
            ORDER BY c.complaint_id DESC
        """)
        rows = cursor.fetchall()
        return [
            {
                "complaint_id": r[0], "complaint_title": r[1],
                "complaint_description": r[2], "status": r[3],
                "created_at": str(r[4]) if r[4] else None,
                "resident_name": f"{r[5]} {r[6]}" if r[5] else None,
                "apartment_number": r[7],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_all_complaints error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch complaints")


def update_complaint_status(conn, complaint_id: int, status: str):
    try:
        valid_statuses = ["pending", "in_progress", "resolved", "closed"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        cursor = conn.cursor()
        cursor.execute("SELECT complaint_id FROM complaint WHERE complaint_id = %s", (complaint_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Complaint not found")
        cursor.execute("UPDATE complaint SET status = %s WHERE complaint_id = %s", (status, complaint_id))
        conn.commit()
        return {"success": True, "message": f"Complaint status updated to '{status}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_complaint_status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update complaint status")