from fastapi import APIRouter, Depends
from app.database import get_db
from app.services import payment_service
from app.routers.dependencies import get_current_user, get_resident_id

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.get("/my-bills")
def get_bills(conn=Depends(get_db), user: dict = Depends(get_current_user)):
    res_id = get_resident_id(conn, user["username"])
    return payment_service.get_my_bills(conn, res_id)

@router.post("/pay/{bill_id}")
def process_payment(bill_id: int, data: dict, conn=Depends(get_db), user: dict = Depends(get_current_user)):
    res_id = get_resident_id(conn, user["username"])
    return payment_service.pay_bill(conn, res_id, bill_id, data.get("payment_method_id"))