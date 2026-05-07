import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def get_payment_methods(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT payment_method_id, method_name FROM payment_method ORDER BY payment_method_id")
        rows = cursor.fetchall()
        return [{"payment_method_id": r[0], "method_name": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"get_payment_methods error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment methods")


def get_my_bills(conn, resident_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mb.bill_id, mb.amount, mb.status, mb.created_at, mb.due_date,
                   pm.method_name, e.f_name, e.l_name, e.job_type
            FROM maintance_bill mb
            LEFT JOIN booking b ON b.booking_id = mb.booking_id
            LEFT JOIN payment_method pm ON pm.payment_method_id = mb.payment_method_id
            LEFT JOIN maintenance_employee e ON e.employee_id = b.employee_id
            WHERE b.resident_id = %s ORDER BY mb.bill_id DESC
        """, (resident_id,))
        rows = cursor.fetchall()
        return [
            {
                "bill_id": r[0], "amount": float(r[1]) if r[1] else None,
                "status": r[2], "created_at": str(r[3]) if r[3] else None,
                "due_date": str(r[4]) if r[4] else None, "payment_method": r[5],
                "employee": f"{r[6]} {r[7]}" if r[6] else None, "service_type": r[8],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_my_bills error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bills")


def pay_bill(conn, resident_id: int, bill_id: int, payment_method_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mb.bill_id, mb.status FROM maintance_bill mb
            JOIN booking b ON b.booking_id = mb.booking_id
            WHERE mb.bill_id = %s AND b.resident_id = %s
        """, (bill_id, resident_id))
        bill = cursor.fetchone()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found or not yours")
        if bill[1] == "paid":
            raise HTTPException(status_code=400, detail="Bill already paid")
        cursor.execute("SELECT payment_method_id FROM payment_method WHERE payment_method_id = %s", (payment_method_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Payment method not found")
        cursor.execute("UPDATE maintance_bill SET status = 'paid', payment_method_id = %s WHERE bill_id = %s", (payment_method_id, bill_id))
        conn.commit()
        return {"success": True, "message": "Bill paid successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"pay_bill error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process payment")