import logging
from pyodbc import Connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Get All Services ──────────────────────────────────────────
def get_all_services(conn: Connection):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id, major_name FROM Maintenance_Major ORDER BY major_id")
        rows = cursor.fetchall()
        return [{"major_id": r.major_id, "major_name": r.major_name} for r in rows]
    except Exception as e:
        logger.error(f"get_all_services error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch services")


# ── Get Service By ID ─────────────────────────────────────────
def get_service_by_id(conn: Connection, service_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id, major_name FROM Maintenance_Major WHERE major_id = ?", service_id)
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"major_id": row.major_id, "major_name": row.major_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_service_by_id error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service")


# ── Add Service (Admin) ───────────────────────────────────────
def add_service(conn: Connection, major_name: str):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id FROM Maintenance_Major WHERE LOWER(major_name) = LOWER(?)", major_name)
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Service already exists")

        cursor.execute("INSERT INTO Maintenance_Major (major_name) VALUES (?)", major_name)
        conn.commit()

        cursor.execute("SELECT TOP 1 major_id FROM Maintenance_Major ORDER BY major_id DESC")
        new_service = cursor.fetchone()

        logger.info(f"Service added: {major_name}")
        return {"success": True, "message": "Service added successfully", "major_id": new_service.major_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"add_service error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add service")


# ── Update Service (Admin) ────────────────────────────────────
def update_service(conn: Connection, service_id: int, major_name: str):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id FROM Maintenance_Major WHERE major_id = ?", service_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Service not found")

        cursor.execute("UPDATE Maintenance_Major SET major_name = ? WHERE major_id = ?", major_name, service_id)
        conn.commit()

        logger.info(f"Service {service_id} updated to {major_name}")
        return {"success": True, "message": "Service updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_service error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update service")


# ── Delete Service (Admin) ────────────────────────────────────
def delete_service(conn: Connection, service_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT major_id FROM Maintenance_Major WHERE major_id = ?", service_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Service not found")

        cursor.execute("DELETE FROM Maintenance_Major WHERE major_id = ?", service_id)
        conn.commit()

        logger.info(f"Service {service_id} deleted")
        return {"success": True, "message": "Service deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"delete_service error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete service")


# ── Professionals ─────────────────────────────────────────────
def get_professionals_by_category(conn: Connection, category: str):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                e.employee_id, e.f_name, e.l_name, e.job_type, e.rating,
                e.home_service, e.night_service, e.is_emergency,
                e.availability, e.profile_image, e.employee_di
            FROM Maintenance_employee e
            WHERE LOWER(e.job_type) = LOWER(?)
            ORDER BY e.rating DESC, e.is_emergency ASC
        """, category)
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No professionals found for category: {category}")
        return [
            {
                "employee_id":   r.employee_id,
                "f_name":        r.f_name,
                "l_name":        r.l_name,
                "job_type":      r.job_type,
                "rating":        r.rating,
                "home_service":  r.home_service,
                "night_service": r.night_service,
                "is_emergency":  bool(r.is_emergency),
                "availability":  bool(r.availability),
                "profile_image": r.profile_image,
                "employee_di":   r.employee_di,
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_professionals_by_category error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch professionals")


# ── Create Booking ────────────────────────────────────────────
def create_booking(conn: Connection, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT employee_id, availability FROM Maintenance_employee WHERE employee_id = ?",
            data["employee_id"]
        )
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Professional not found")
        if not emp.availability:
            raise HTTPException(status_code=400, detail="Professional is not available right now")

        if data.get("payment_method_id"):
            cursor.execute(
                "SELECT payment_method_id FROM Payment_method WHERE payment_method_id = ?",
                data["payment_method_id"]
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Payment method not found")

        cursor.execute("""
            INSERT INTO Booking
                (resident_id, employee_id, service_type, scheduled_date,
                 is_emergency, notes, payment_method_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            resident_id, data["employee_id"], data["service_type"],
            data.get("scheduled_date"), 1 if data.get("is_emergency") else 0,
            data.get("notes"), data.get("payment_method_id"),
        )

        cursor.execute(
            "UPDATE Resident SET total_requests = total_requests + 1 WHERE resident_id = ?",
            resident_id
        )
        conn.commit()

        cursor.execute("SELECT TOP 1 booking_id FROM Booking WHERE resident_id = ? ORDER BY booking_id DESC", resident_id)
        new_booking = cursor.fetchone()

        logger.info(f"Booking created: {new_booking.booking_id} for resident {resident_id}")
        return {"success": True, "message": "Booking created successfully", "booking_id": new_booking.booking_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"create_booking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create booking")


# ── Get My Bookings ───────────────────────────────────────────
def get_my_bookings(conn: Connection, resident_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                b.booking_id, b.service_type, b.scheduled_date, b.is_emergency,
                b.notes, b.status, b.created_at,
                e.f_name AS emp_f_name, e.l_name AS emp_l_name,
                e.job_type, e.rating AS emp_rating,
                pm.method_name AS payment_method
            FROM Booking b
            LEFT JOIN Maintenance_employee e ON e.employee_id = b.employee_id
            LEFT JOIN Payment_method pm ON pm.payment_method_id = b.payment_method_id
            WHERE b.resident_id = ?
            ORDER BY b.booking_id DESC
        """, resident_id)
        rows = cursor.fetchall()
        return [
            {
                "booking_id":     r.booking_id,
                "service_type":   r.service_type,
                "scheduled_date": str(r.scheduled_date) if r.scheduled_date else None,
                "is_emergency":   bool(r.is_emergency),
                "notes":          r.notes,
                "status":         r.status,
                "created_at":     str(r.created_at) if r.created_at else None,
                "employee":       f"{r.emp_f_name} {r.emp_l_name}" if r.emp_f_name else None,
                "job_type":       r.job_type,
                "emp_rating":     r.emp_rating,
                "payment_method": r.payment_method,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_bookings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")


# ── Get All Bookings (Admin) ──────────────────────────────────
def get_all_bookings(conn: Connection):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                b.booking_id, b.service_type, b.scheduled_date, b.is_emergency,
                b.notes, b.status, b.created_at,
                r.f_name AS res_f_name, r.l_name AS res_l_name, r.apartment_number,
                e.f_name AS emp_f_name, e.l_name AS emp_l_name, e.job_type,
                pm.method_name AS payment_method
            FROM Booking b
            LEFT JOIN Resident r ON r.resident_id = b.resident_id
            LEFT JOIN Maintenance_employee e ON e.employee_id = b.employee_id
            LEFT JOIN Payment_method pm ON pm.payment_method_id = b.payment_method_id
            ORDER BY b.booking_id DESC
        """)
        rows = cursor.fetchall()
        return [
            {
                "booking_id":       r.booking_id,
                "service_type":     r.service_type,
                "scheduled_date":   str(r.scheduled_date) if r.scheduled_date else None,
                "is_emergency":     bool(r.is_emergency),
                "notes":            r.notes,
                "status":           r.status,
                "created_at":       str(r.created_at) if r.created_at else None,
                "resident":         f"{r.res_f_name} {r.res_l_name}" if r.res_f_name else None,
                "apartment_number": r.apartment_number,
                "employee":         f"{r.emp_f_name} {r.emp_l_name}" if r.emp_f_name else None,
                "job_type":         r.job_type,
                "payment_method":   r.payment_method,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_all_bookings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")


# ── Update Booking Status (Admin) ─────────────────────────────
def update_booking_status(conn: Connection, booking_id: int, status: str):
    try:
        valid_statuses = ["pending", "confirmed", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        cursor = conn.cursor()
        cursor.execute("SELECT booking_id FROM Booking WHERE booking_id = ?", booking_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Booking not found")

        cursor.execute("UPDATE Booking SET status = ? WHERE booking_id = ?", status, booking_id)
        conn.commit()

        logger.info(f"Booking {booking_id} status updated to {status}")
        return {"success": True, "message": f"Booking status updated to '{status}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_booking_status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update booking status")


# ── Cancel Booking ────────────────────────────────────────────
def cancel_booking(conn: Connection, resident_id: int, booking_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT booking_id, status FROM Booking WHERE booking_id = ? AND resident_id = ?",
            booking_id, resident_id
        )
        booking = cursor.fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found or not yours")
        if booking.status in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel a {booking.status} booking")

        cursor.execute("UPDATE Booking SET status = 'cancelled' WHERE booking_id = ?", booking_id)
        conn.commit()

        logger.info(f"Booking {booking_id} cancelled by resident {resident_id}")
        return {"success": True, "message": "Booking cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cancel_booking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel booking")


# ── User Profile ──────────────────────────────────────────────
def get_user_profile(conn: Connection, username: str):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                l.username, l.email, l.user_role,
                r.f_name, r.l_name,
                r.resident_phone_num AS phone,
                r.area, r.apartment_number, r.unit_number,
                r.joining_date, r.total_requests
            FROM Login l
            LEFT JOIN Resident r ON r.email = l.email
            WHERE l.username = ?
        """, username)
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "username":         row.username,
            "email":            row.email,
            "role":             row.user_role,
            "f_name":           row.f_name,
            "l_name":           row.l_name,
            "phone":            row.phone,
            "area":             row.area,
            "apartment_number": row.apartment_number,
            "unit_number":      row.unit_number,
            "joining_date":     str(row.joining_date) if row.joining_date else None,
            "total_requests":   row.total_requests,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_user_profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")
