from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import get_db
from app.services import payment_service
from app.routers.dependencies import get_current_user, get_resident_id

router = APIRouter(prefix="/payments", tags=["Payments"])


# ── Schemas ───────────────────────────────────────────────────
class PayBillRequest(BaseModel):
    payment_method_id: int


# ── Routes ────────────────────────────────────────────────────
@router.get("/methods")
def get_payment_methods(conn=Depends(get_db)):
    """Get all available payment methods. Public endpoint."""
    return payment_service.get_payment_methods(conn)


@router.get("/my-bills")
def my_bills(
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all bills for the logged-in resident."""
    resident_id = get_resident_id(conn, current_user["username"])
    return payment_service.get_my_bills(conn, resident_id)


@router.post("/pay/{bill_id}")
def pay_bill(
    bill_id: int,
    data: PayBillRequest,
    conn=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pay a specific bill. Requires authentication."""
    resident_id = get_resident_id(conn, current_user["username"])
    return payment_service.pay_bill(conn, resident_id, bill_id, data.payment_method_id)
