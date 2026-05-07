import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Services ──────────────────────────────────────────────────
def get_all_services(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id, major_name FROM maintenance_major ORDER BY major_id")
        rows = cursor.fetchall()
        return [{"major_id": r[0], "major_name": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"get_all_services error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch services")

def get_service_by_id(conn, service_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id, major_name FROM maintenance_major WHERE major_id = %s", (service_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"major_id": row[0], "major_name": row[1]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_service_by_id error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service")

def add_service(conn, major_name: str):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id FROM maintenance_major WHERE LOWER(major_name) = LOWER(%s)", (major_name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Service already exists")
        cursor.execute("INSERT INTO maintenance_major (major_name) VALUES (%s)", (major_name,))
        conn.commit()
        cursor.execute("SELECT major_id FROM maintenance_major ORDER BY major_id DESC LIMIT 1")
        new_service = cursor.fetchone()
        return {"success": True, "message": "Service added successfully", "major_id": new_service[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"add_service error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add service")

def update_service(conn, service_id: int, major_name: str):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id FROM maintenance_major WHERE major_id = %s", (service_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Service not found")
        cursor.execute("UPDATE maintenance_major SET major_name = %s WHERE major_id = %s", (major_name, service_id))
        conn.commit()
        return {"success": True, "message": "Service updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_service error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update service")

def delete_service(conn, service_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id FROM maintenance_major WHERE major_id = %s", (service_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Service not found")
        cursor.execute("DELETE FROM maintenance_major WHERE major_id = %s", (service_id,))
        conn.commit()
        return {"success": True, "message": "Service deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"delete_service error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete service")


# ── Professionals ─────────────────────────────────────────────
def get_professionals_by_category(conn, category: str):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.employee_id, e.f_name, e.l_name, e.job_type, e.rating,
                   e.home_service, e.night_service, e.is_emergency,
                   e.availability, e.profile_image, e.employee_di
            FROM maintenance_employee e
            WHERE LOWER(e.job_type) = LOWER(%s)
            ORDER BY e.rating DESC, e.is_emergency ASC
        """, (category,))
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No professionals found for category: {category}")
        return [
            {
                "employee_id":   r[0], "f_name": r[1], "l_name": r[2],
                "job_type":      r[3], "rating": r[4], "home_service": r[5],
                "night_service": r[6], "is_emergency": bool(r[7]),
                "availability":  bool(r[8]), "profile_image": r[9], "employee_di": r[10],
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_professionals_by_category error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch professionals")


# ── Booking ───────────────────────────────────────────────────
def create_booking(conn, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT employee_id, availability FROM maintenance_employee WHERE employee_id = %s", (data["employee_id"],))
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Professional not found")
        if not emp[1]:
            raise HTTPException(status_code=400, detail="Professional is not available right now")

        if data.get("payment_method_id"):
            cursor.execute("SELECT payment_method_id FROM payment_method WHERE payment_method_id = %s", (data["payment_method_id"],))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Payment method not found")

        cursor.execute("""
            INSERT INTO booking (resident_id, employee_id, service_type, scheduled_date, is_emergency, notes, payment_method_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (resident_id, data["employee_id"], data["service_type"],
              data.get("scheduled_date"), 1 if data.get("is_emergency") else 0,
              data.get("notes"), data.get("payment_method_id")))

        cursor.execute("UPDATE resident SET total_requests = total_requests + 1 WHERE resident_id = %s", (resident_id,))
        conn.commit()
        cursor.execute("SELECT booking_id FROM booking WHERE resident_id = %s ORDER BY booking_id DESC LIMIT 1", (resident_id,))
        new_booking = cursor.fetchone()
        return {"success": True, "message": "Booking created successfully", "booking_id": new_booking[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"create_booking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create booking")

def get_my_bookings(conn, resident_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.booking_id, b.service_type, b.scheduled_date, b.is_emergency,
                   b.notes, b.status, b.created_at,
                   e.f_name, e.l_name, e.job_type, e.rating, pm.method_name
            FROM booking b
            LEFT JOIN maintenance_employee e ON e.employee_id = b.employee_id
            LEFT JOIN payment_method pm ON pm.payment_method_id = b.payment_method_id
            WHERE b.resident_id = %s ORDER BY b.booking_id DESC
        """, (resident_id,))
        rows = cursor.fetchall()
        return [
            {
                "booking_id": r[0], "service_type": r[1],
                "scheduled_date": str(r[2]) if r[2] else None,
                "is_emergency": bool(r[3]), "notes": r[4], "status": r[5],
                "created_at": str(r[6]) if r[6] else None,
                "employee": f"{r[7]} {r[8]}" if r[7] else None,
                "job_type": r[9], "emp_rating": r[10], "payment_method": r[11],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_bookings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")

def get_all_bookings(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.booking_id, b.service_type, b.scheduled_date, b.is_emergency,
                   b.notes, b.status, b.created_at,
                   r.f_name, r.l_name, r.apartment_number,
                   e.f_name, e.l_name, e.job_type, pm.method_name
            FROM booking b
            LEFT JOIN resident r ON r.resident_id = b.resident_id
            LEFT JOIN maintenance_employee e ON e.employee_id = b.employee_id
            LEFT JOIN payment_method pm ON pm.payment_method_id = b.payment_method_id
            ORDER BY b.booking_id DESC
        """)
        rows = cursor.fetchall()
        return [
            {
                "booking_id": r[0], "service_type": r[1],
                "scheduled_date": str(r[2]) if r[2] else None,
                "is_emergency": bool(r[3]), "notes": r[4], "status": r[5],
                "created_at": str(r[6]) if r[6] else None,
                "resident": f"{r[7]} {r[8]}" if r[7] else None,
                "apartment_number": r[9],
                "employee": f"{r[10]} {r[11]}" if r[10] else None,
                "job_type": r[12], "payment_method": r[13],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_all_bookings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")

def update_booking_status(conn, booking_id: int, status: str):
    try:
        valid_statuses = ["pending", "confirmed", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        cursor = conn.cursor()
        cursor.execute("SELECT booking_id FROM booking WHERE booking_id = %s", (booking_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Booking not found")
        cursor.execute("UPDATE booking SET status = %s WHERE booking_id = %s", (status, booking_id))
        conn.commit()
        return {"success": True, "message": f"Booking status updated to '{status}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_booking_status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update booking status")

def cancel_booking(conn, resident_id: int, booking_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT booking_id, status FROM booking WHERE booking_id = %s AND resident_id = %s", (booking_id, resident_id))
        booking = cursor.fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found or not yours")
        if booking[1] in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel a {booking[1]} booking")
        cursor.execute("UPDATE booking SET status = 'cancelled' WHERE booking_id = %s", (booking_id,))
        conn.commit()
        return {"success": True, "message": "Booking cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cancel_booking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel booking")


# ── User Profile ──────────────────────────────────────────────
def get_user_profile(conn, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.username, l.email, l.user_role,
                   r.f_name, r.l_name, r.resident_phone_num,
                   r.area, r.apartment_number, r.unit_number,
                   r.joining_date, r.total_requests
            FROM login l
            LEFT JOIN resident r ON r.email = l.email
            WHERE l.username = %s
        """, (username,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "username": row[0], "email": row[1], "role": row[2],
            "f_name": row[3], "l_name": row[4], "phone": row[5],
            "area": row[6], "apartment_number": row[7], "unit_number": row[8],
            "joining_date": str(row[9]) if row[9] else None, "total_requests": row[10],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_user_profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")