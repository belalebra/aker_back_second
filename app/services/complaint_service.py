import logging
from pyodbc import Connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Submit Complaint ──────────────────────────────────────────
def submit_complaint(conn: Connection, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()

        # Validate resident exists
        cursor.execute("SELECT resident_id FROM Resident WHERE resident_id = ?", resident_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Resident not found")

        cursor.execute("""
            INSERT INTO Complaint (resident_id, complaint_title, complaint_description, status)
            VALUES (?, ?, ?, 'pending')
        """,
            resident_id,
            data["complaint_title"],
            data["complaint_description"],
        )
        conn.commit()

        cursor.execute(
            "SELECT TOP 1 complaint_id FROM Complaint WHERE resident_id = ? ORDER BY complaint_id DESC",
            resident_id
        )
        new_complaint = cursor.fetchone()

        logger.info(f"Complaint submitted: {new_complaint.complaint_id} by resident {resident_id}")
        return {
            "success": True,
            "message": "Complaint submitted successfully",
            "complaint_id": new_complaint.complaint_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"submit_complaint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit complaint")


# ── Get My Complaints ─────────────────────────────────────────
def get_my_complaints(conn: Connection, resident_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT complaint_id, complaint_title, complaint_description, status, created_at
            FROM Complaint
            WHERE resident_id = ?
            ORDER BY complaint_id DESC
        """, resident_id)
        rows = cursor.fetchall()

        return [
            {
                "complaint_id":          r.complaint_id,
                "complaint_title":       r.complaint_title,
                "complaint_description": r.complaint_description,
                "status":                r.status,
                "created_at":            str(r.created_at) if r.created_at else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_complaints error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch complaints")


# ── Get All Complaints (Admin) ────────────────────────────────
def get_all_complaints(conn: Connection):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.complaint_id,
                c.complaint_title,
                c.complaint_description,
                c.status,
                c.created_at,
                r.f_name,
                r.l_name,
                r.apartment_number
            FROM Complaint c
            LEFT JOIN Resident r ON r.resident_id = c.resident_id
            ORDER BY c.complaint_id DESC
        """)
        rows = cursor.fetchall()

        return [
            {
                "complaint_id":          r.complaint_id,
                "complaint_title":       r.complaint_title,
                "complaint_description": r.complaint_description,
                "status":                r.status,
                "created_at":            str(r.created_at) if r.created_at else None,
                "resident_name":         f"{r.f_name} {r.l_name}" if r.f_name else None,
                "apartment_number":      r.apartment_number,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_all_complaints error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch complaints")


# ── Update Complaint Status (Admin) ───────────────────────────
def update_complaint_status(conn: Connection, complaint_id: int, status: str):
    try:
        valid_statuses = ["pending", "in_progress", "resolved", "closed"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        cursor = conn.cursor()
        cursor.execute("SELECT complaint_id FROM Complaint WHERE complaint_id = ?", complaint_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Complaint not found")

        cursor.execute(
            "UPDATE Complaint SET status = ? WHERE complaint_id = ?",
            status, complaint_id
        )
        conn.commit()

        logger.info(f"Complaint {complaint_id} status updated to {status}")
        return {"success": True, "message": f"Complaint status updated to '{status}'"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_complaint_status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update complaint status")
