import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db
from app.services.auth_service import get_user_by_username, is_token_blacklisted
from app.core.config import SECRET_KEY, ALGORITHM

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn=Depends(get_db)
):
    token = credentials.credentials
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked, please login again")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = get_user_by_username(conn, username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user


def get_resident_id(conn, username: str) -> int:
    user = get_user_by_username(conn, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cursor = conn.cursor()
    cursor.execute("SELECT resident_id FROM resident WHERE email = %s", (user[4],))
    resident = cursor.fetchone()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    return resident[0]