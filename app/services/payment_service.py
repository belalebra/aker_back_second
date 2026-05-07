import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def get_my_bills(conn, resident_id: int):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mb.*, pm.method_name as payment_method
        FROM maintance_bill mb
        LEFT JOIN booking b ON b.booking_id = mb.booking_id
        LEFT JOIN payment_method pm ON pm.payment_method_id = mb.payment_method_id
        WHERE b.resident_id = %s ORDER BY mb.created_at DESC
    """, (resident_id,))
    rows = cursor.fetchall()
    for r in rows:
        r["amount"] = float(r["amount"]) if r["amount"] else 0.0
        r["due_date"] = str(r["due_date"]) if r["due_date"] else None
    return rows

def pay_bill(conn, resident_id: int, bill_id: int, payment_method_id: int):
    try:
        cursor = conn.cursor()
        # Verify ownership
        cursor.execute("""
            SELECT 1 FROM maintance_bill mb 
            JOIN booking b ON b.booking_id = mb.booking_id
            WHERE mb.bill_id = %s AND b.resident_id = %s AND mb.status != 'paid'
        """, (bill_id, resident_id))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Bill not found or already paid")

        cursor.execute("UPDATE maintance_bill SET status = 'paid', payment_method_id = %s WHERE bill_id = %s", 
                       (payment_method_id, bill_id))
        conn.commit()
        return {"success": True, "message": "Payment successful"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))