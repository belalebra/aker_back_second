from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import get_db
from app.services import payment_service
from app.routers.dependencies import get_current_user, get_resident_id

router = APIRouter(prefix="/payments", tags=["Payments"])


class PayBillRequest(BaseModel):
    payment_method_id: int


@router.get("/methods")
def get_payment_methods(conn=Depends(get_db)):
    return payment_service.get_payment_methods(conn)


@router.get("/my-bills")
def my_bills(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    resident_id = get_resident_id(conn, current_user["username"])
    return payment_service.get_my_bills(conn, resident_id)


@router.post("/pay/{bill_id}")
def pay_bill(bill_id: int, data: PayBillRequest, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    resident_id = get_resident_id(conn, current_user["username"])
    return payment_service.pay_bill(conn, resident_id, bill_id, data.payment_method_id)