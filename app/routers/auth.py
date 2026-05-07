from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from app.schemas.auth import LoginRequest, RegisterRequest
from app.database import get_db
from app.services import auth_service
from app.routers.dependencies import get_current_user, get_current_admin
import jwt
from app.core.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


class RefreshRequest(BaseModel):
    refresh_token: str

class ResetRequest(BaseModel):
    email: EmailStr

class ConfirmResetRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str


@router.post("/login")
def login(data: LoginRequest, conn=Depends(get_db)):
    return auth_service.login_user(conn, data.username, data.password)


@router.post("/register")
def register(data: RegisterRequest, conn=Depends(get_db)):
    return auth_service.register_user(conn, data.username, data.password, data.email, data.phone)


@router.post("/register-admin")
def register_admin(data: RegisterRequest, conn=Depends(get_db), _: dict = Depends(get_current_admin)):
    return auth_service.register_user(conn, data.username, data.password, data.email, role="admin")


@router.post("/refresh")
def refresh_token(data: RefreshRequest, conn=Depends(get_db)):
    return auth_service.refresh_access_token(conn, data.refresh_token)


@router.post("/password-reset/request")
def request_reset(data: ResetRequest, conn=Depends(get_db)):
    return auth_service.request_password_reset(conn, data.email)


@router.post("/password-reset/confirm")
def confirm_reset(data: ConfirmResetRequest, conn=Depends(get_db)):
    return auth_service.confirm_password_reset(conn, data.email, data.token, data.new_password)


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user.get("username"), "role": current_user.get("role")}


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security), current_user: dict = Depends(get_current_user)):
    auth_service.blacklist_token(credentials.credentials)
    return {"success": True, "message": "Logged out successfully"}