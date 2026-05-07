from fastapi import APIRouter, Depends
from app.database import get_db
from app.services import auth_service
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def login(data: LoginRequest, conn=Depends(get_db)):
    return auth_service.login_user(conn, data.username, data.password)

@router.post("/register")
def register(data: RegisterRequest, conn=Depends(get_db)):
    return auth_service.register_user(conn, data.username, data.password, data.email, data.phone)