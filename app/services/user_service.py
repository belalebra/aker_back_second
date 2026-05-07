import logging
from fastapi import HTTPException
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_profile(conn, username: str):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.username, l.email, l.user_role as role,
               r.f_name, r.l_name, r.area, r.apartment_number, r.joining_date
        FROM login l
        LEFT JOIN resident r ON r.email = l.email
        WHERE l.username = %s
    """, (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("joining_date"):
        user["joining_date"] = str(user["joining_date"])
    return user

def update_my_profile(conn, username: str, data: dict):
    try:
        cursor = conn.cursor()
        if data.get("phone"):
            cursor.execute("UPDATE login SET phone = %s WHERE username = %s", (data["phone"], username))
        
        cursor.execute("SELECT email FROM login WHERE username = %s", (username,))
        email = cursor.fetchone()["email"]
        
        # Update Resident table
        if any(k in data for k in ["f_name", "l_name"]):
            cursor.execute("""
                UPDATE resident SET f_name = COALESCE(%s, f_name), l_name = COALESCE(%s, l_name)
                WHERE email = %s
            """, (data.get("f_name"), data.get("l_name"), email))
            
        conn.commit()
        return {"success": True, "message": "Profile updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))