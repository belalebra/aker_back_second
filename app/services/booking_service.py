import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def get_all_services(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT major_id, major_name FROM maintenance_major ORDER BY major_id")
    return cursor.fetchall()

def get_professionals_by_category(conn, category: str):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT employee_id, f_name, l_name, job_type, rating, availability, profile_image
        FROM maintenance_employee
        WHERE LOWER(job_type) = LOWER(%s)
        ORDER BY rating DESC
    """, (category,))
    rows = cursor.fetchall()
    for r in rows:
        r["availability"] = bool(r["availability"])
    return rows

def create_booking(conn, resident_id: int, data: dict):
    try:
        cursor = conn.cursor()
        # Create booking and get ID back instantly
        cursor.execute("""
            INSERT INTO booking (resident_id, employee_id, service_type, scheduled_date, is_emergency, notes, payment_method_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING booking_id
        """, (resident_id, data["employee_id"], data["service_type"], 
              data.get("scheduled_date"), 1 if data.get("is_emergency") else 0, 
              data.get("notes"), data.get("payment_method_id")))
        
        booking_id = cursor.fetchone()["booking_id"]
        
        # Update resident stats
        cursor.execute("UPDATE resident SET total_requests = total_requests + 1 WHERE resident_id = %s", (resident_id,))
        
        conn.commit()
        return {"success": True, "booking_id": booking_id, "message": "Booking successful"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Booking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create booking")

def get_my_bookings(conn, resident_id: int):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, e.f_name as emp_f, e.l_name as emp_l, pm.method_name as payment_method
        FROM booking b
        LEFT JOIN maintenance_employee e ON e.employee_id = b.employee_id
        LEFT JOIN payment_method pm ON pm.payment_method_id = b.payment_method_id
        WHERE b.resident_id = %s ORDER BY b.created_at DESC
    """, (resident_id,))
    rows = cursor.fetchall()
    for r in rows:
        r["scheduled_date"] = str(r["scheduled_date"]) if r["scheduled_date"] else None
        r["created_at"] = str(r["created_at"]) if r["created_at"] else None
        r["employee_name"] = f"{r['emp_f']} {r['emp_l']}".strip() if r.get("emp_f") else "Pending"
    return rows