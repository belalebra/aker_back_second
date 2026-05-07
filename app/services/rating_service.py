import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def submit_rating(conn, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT booking_id, employee_id, status FROM booking WHERE booking_id = %s AND resident_id = %s", (data["booking_id"], resident_id))
        booking = cursor.fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found or not yours")
        if booking[2] != "completed":
            raise HTTPException(status_code=400, detail="Can only rate completed bookings")
        cursor.execute("SELECT rating_id FROM employee_rating WHERE booking_id = %s AND resident_id = %s", (data["booking_id"], resident_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="You already rated this booking")
        rating_value = data["rating"]
        if not (1 <= rating_value <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        cursor.execute("""
            INSERT INTO employee_rating (employee_id, resident_id, booking_id, rating, review)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking[1], resident_id, data["booking_id"], rating_value, data.get("review")))
        cursor.execute("""
            UPDATE maintenance_employee SET rating = (
                SELECT AVG(CAST(rating AS FLOAT)) FROM employee_rating WHERE employee_id = %s
            ) WHERE employee_id = %s
        """, (booking[1], booking[1]))
        conn.commit()
        return {"success": True, "message": "Rating submitted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"submit_rating error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit rating")


def get_employee_ratings(conn, employee_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT employee_id, rating FROM maintenance_employee WHERE employee_id = %s", (employee_id,))
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        cursor.execute("""
            SELECT er.rating_id, er.rating, er.review, er.created_at, r.f_name, r.l_name
            FROM employee_rating er
            LEFT JOIN resident r ON r.resident_id = er.resident_id
            WHERE er.employee_id = %s ORDER BY er.rating_id DESC
        """, (employee_id,))
        rows = cursor.fetchall()
        return {
            "employee_id": employee_id, "average_rating": emp[1], "total_ratings": len(rows),
            "ratings": [
                {
                    "rating_id": r[0], "rating": r[1], "review": r[2],
                    "created_at": str(r[3]) if r[3] else None,
                    "resident": f"{r[4]} {r[5]}" if r[4] else "Anonymous",
                }
                for r in rows
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_employee_ratings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ratings")