import logging
from pyodbc import Connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Submit Rating ─────────────────────────────────────────────
def submit_rating(conn: Connection, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()

        # Validate booking belongs to this resident and is completed
        cursor.execute("""
            SELECT booking_id, employee_id, status
            FROM Booking
            WHERE booking_id = ? AND resident_id = ?
        """, data["booking_id"], resident_id)
        booking = cursor.fetchone()

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found or not yours")
        if booking.status != "completed":
            raise HTTPException(status_code=400, detail="Can only rate completed bookings")

        # Check not rated before
        cursor.execute("""
            SELECT rating_id FROM Employee_Rating
            WHERE booking_id = ? AND resident_id = ?
        """, data["booking_id"], resident_id)
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="You already rated this booking")

        rating_value = data["rating"]
        if not (1 <= rating_value <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

        # Insert rating
        cursor.execute("""
            INSERT INTO Employee_Rating (employee_id, resident_id, booking_id, rating, review)
            VALUES (?, ?, ?, ?, ?)
        """, booking.employee_id, resident_id, data["booking_id"], rating_value, data.get("review"))

        # Recalculate employee average rating
        cursor.execute("""
            UPDATE Maintenance_employee
            SET rating = (
                SELECT AVG(CAST(rating AS FLOAT))
                FROM Employee_Rating
                WHERE employee_id = ?
            )
            WHERE employee_id = ?
        """, booking.employee_id, booking.employee_id)

        conn.commit()

        logger.info(f"Rating submitted for employee {booking.employee_id} by resident {resident_id}")
        return {"success": True, "message": "Rating submitted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"submit_rating error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit rating")


# ── Get Employee Ratings ──────────────────────────────────────
def get_employee_ratings(conn: Connection, employee_id: int):
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT employee_id, rating FROM Maintenance_employee WHERE employee_id = ?", employee_id)
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        cursor.execute("""
            SELECT
                er.rating_id, er.rating, er.review, er.created_at,
                r.f_name, r.l_name
            FROM Employee_Rating er
            LEFT JOIN Resident r ON r.resident_id = er.resident_id
            WHERE er.employee_id = ?
            ORDER BY er.rating_id DESC
        """, employee_id)
        rows = cursor.fetchall()

        return {
            "employee_id":    employee_id,
            "average_rating": emp.rating,
            "total_ratings":  len(rows),
            "ratings": [
                {
                    "rating_id":   r.rating_id,
                    "rating":      r.rating,
                    "review":      r.review,
                    "created_at":  str(r.created_at) if r.created_at else None,
                    "resident":    f"{r.f_name} {r.l_name}" if r.f_name else "Anonymous",
                }
                for r in rows
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_employee_ratings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ratings")
