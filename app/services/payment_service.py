import logging
from pyodbc import Connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Get All Payment Methods ───────────────────────────────────
def get_payment_methods(conn: Connection):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT payment_method_id, method_name FROM Payment_method ORDER BY payment_method_id")
        rows = cursor.fetchall()
        return [
            {"payment_method_id": r.payment_method_id, "method_name": r.method_name}
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_payment_methods error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment methods")


# ── Get My Bills ──────────────────────────────────────────────
def get_my_bills(conn: Connection, resident_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                mb.bill_id,
                mb.amount,
                mb.status,
                mb.created_at,
                mb.due_date,
                pm.method_name AS payment_method,
                e.f_name AS emp_f_name,
                e.l_name AS emp_l_name,
                e.job_type
            FROM Maintance_bill mb
            LEFT JOIN Booking b       ON b.booking_id = mb.booking_id
            LEFT JOIN Payment_method pm ON pm.payment_method_id = mb.payment_method_id
            LEFT JOIN Maintenance_employee e ON e.employee_id = b.employee_id
            WHERE b.resident_id = ?
            ORDER BY mb.bill_id DESC
        """, resident_id)
        rows = cursor.fetchall()

        return [
            {
                "bill_id":        r.bill_id,
                "amount":         float(r.amount) if r.amount else None,
                "status":         r.status,
                "created_at":     str(r.created_at) if r.created_at else None,
                "due_date":       str(r.due_date) if r.due_date else None,
                "payment_method": r.payment_method,
                "employee":       f"{r.emp_f_name} {r.emp_l_name}" if r.emp_f_name else None,
                "service_type":   r.job_type,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_bills error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bills")


# ── Pay Bill ──────────────────────────────────────────────────
def pay_bill(conn: Connection, resident_id: int, bill_id: int, payment_method_id: int):
    try:
        cursor = conn.cursor()

        # Validate bill belongs to this resident
        cursor.execute("""
            SELECT mb.bill_id, mb.status
            FROM Maintance_bill mb
            JOIN Booking b ON b.booking_id = mb.booking_id
            WHERE mb.bill_id = ? AND b.resident_id = ?
        """, bill_id, resident_id)
        bill = cursor.fetchone()

        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found or not yours")
        if bill.status == "paid":
            raise HTTPException(status_code=400, detail="Bill already paid")

        # Validate payment method
        cursor.execute(
            "SELECT payment_method_id FROM Payment_method WHERE payment_method_id = ?",
            payment_method_id
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Payment method not found")

        cursor.execute("""
            UPDATE Maintance_bill
            SET status = 'paid', payment_method_id = ?
            WHERE bill_id = ?
        """, payment_method_id, bill_id)
        conn.commit()

        logger.info(f"Bill {bill_id} paid by resident {resident_id}")
        return {"success": True, "message": "Bill paid successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"pay_bill error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process payment")
