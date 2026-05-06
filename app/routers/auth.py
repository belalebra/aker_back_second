from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from app.schemas.auth import LoginRequest, RegisterRequest
from app.database import get_db
from app.services import auth_service
from app.core.config import SECRET_KEY, ALGORITHM
import jwt

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ── Schemas ───────────────────────────────────────────────────
class RefreshRequest(BaseModel):
    refresh_token: str

class ResetRequest(BaseModel):
    email: EmailStr

class ConfirmResetRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str


# ── Auth Helpers ──────────────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn=Depends(get_db)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user


# ── Routes ────────────────────────────────────────────────────
@router.post("/login")
def login(data: LoginRequest, conn=Depends(get_db)):
    return auth_service.login_user(conn, data.username, data.password)


@router.post("/register")
def register(data: RegisterRequest, conn=Depends(get_db)):
    return auth_service.register_user(conn, data.username, data.password, data.email, data.phone)


@router.post("/register-admin")
def register_admin(
    data: RegisterRequest,
    conn=Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Register new admin. Requires admin token."""
    return auth_service.register_user(conn, data.username, data.password, data.email, role="admin")


@router.post("/refresh")
def refresh_token(data: RefreshRequest, conn=Depends(get_db)):
    """Get new access token using refresh token."""
    return auth_service.refresh_access_token(conn, data.refresh_token)


@router.post("/password-reset/request")
def request_reset(data: ResetRequest, conn=Depends(get_db)):
    """Request password reset token."""
    return auth_service.request_password_reset(conn, data.email)


@router.post("/password-reset/confirm")
def confirm_reset(data: ConfirmResetRequest, conn=Depends(get_db)):
    """Confirm password reset with token and new password."""
    return auth_service.confirm_password_reset(conn, data.email, data.token, data.new_password)


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current logged-in user info from token."""
    return {
        "username": current_user.get("username"),
        "role": current_user.get("role")
    }

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user)
):
    """Logout and invalidate the current token."""
    from app.services.auth_service import blacklist_token
    blacklist_token(credentials.credentials)
    return {"success": True, "message": "Logged out successfully"}
