import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db
from app.core.config import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def get_resident_id(conn, username: str) -> int:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.resident_id FROM resident r
        JOIN login l ON l.email = r.email
        WHERE l.username = %s
    """, (username,))
    res = cursor.fetchone()
    if not res:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    return res["resident_id"]