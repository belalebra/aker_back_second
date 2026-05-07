import logging
from psycopg2.extensions import connection as Connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ── Get All Payment Methods ───────────────────────────────────
def get_payment_methods(conn: Connection):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT payment_method_id, method_name FROM payment_method ORDER BY payment_method_id")
        rows = cursor.fetchall()
        return [
            {"payment_method_id": r[0], "method_name": r[1]}
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
            FROM maintance_bill mb
            LEFT JOIN booking b       ON b.booking_id = mb.booking_id
            LEFT JOIN payment_method pm ON pm.payment_method_id = mb.payment_method_id
            LEFT JOIN maintenance_employee e ON e.employee_id = b.employee_id
            WHERE b.resident_id = %s
            ORDER BY mb.bill_id DESC
        """, (resident_id,))
        rows = cursor.fetchall()

        return [
            {
                "bill_id":        r[0],
                "amount":         float(r[1]) if r[1] else None,
                "status":         r[2],
                "created_at":     str(r[3]) if r[3] else None,
                "due_date":       str(r[4]) if r[4] else None,
                "payment_method": r[5],
                "employee":       f"{r[6]} {r[7]}" if r[6] else None,
                "service_type":   r[8],
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
            FROM maintance_bill mb
            JOIN booking b ON b.booking_id = mb.booking_id
            WHERE mb.bill_id = %s AND b.resident_id = %s
        """, (bill_id, resident_id))
        bill = cursor.fetchone()

        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found or not yours")
        if bill[1] == "paid":
            raise HTTPException(status_code=400, detail="Bill already paid")

        # Validate payment method
        cursor.execute(
            "SELECT payment_method_id FROM payment_method WHERE payment_method_id = %s",
            (payment_method_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Payment method not found")

        cursor.execute("""
            UPDATE maintance_bill
            SET status = 'paid', payment_method_id = %s
            WHERE bill_id = %s
        """, (payment_method_id, bill_id))
        conn.commit()

        logger.info(f"Bill {bill_id} paid by resident {resident_id}")
        return {"success": True, "message": "Bill paid successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"pay_bill error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process payment")
