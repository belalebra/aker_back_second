import logging
from fastapi import HTTPException
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_all_users(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.username, l.email, l.user_role, l.phone,
                   r.f_name, r.l_name, r.area, r.apartment_number,
                   r.unit_number, r.joining_date, r.total_requests
            FROM login l
            LEFT JOIN resident r ON r.email = l.email
            ORDER BY l.username
        """)
        rows = cursor.fetchall()
        return [
            {
                "username": r[0], "email": r[1], "role": r[2], "phone": r[3],
                "f_name": r[4], "l_name": r[5], "area": r[6],
                "apartment_number": r[7], "unit_number": r[8],
                "joining_date": str(r[9]) if r[9] else None, "total_requests": r[10],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_all_users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


def update_my_profile(conn, username: str, data: dict):
    try:
        cursor = conn.cursor()
        if data.get("phone"):
            cursor.execute("UPDATE login SET phone = %s WHERE username = %s", (data["phone"], username))
        if data.get("new_password"):
            hashed = pwd_context.hash(data["new_password"])
            cursor.execute("UPDATE login SET user_password = %s WHERE username = %s", (hashed, username))
        cursor.execute("SELECT email FROM login WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        update_fields = []
        update_values = []
        if data.get("f_name"):
            update_fields.append("f_name = %s")
            update_values.append(data["f_name"])
        if data.get("l_name"):
            update_fields.append("l_name = %s")
            update_values.append(data["l_name"])
        if data.get("phone"):
            update_fields.append("resident_phone_num = %s")
            update_values.append(data["phone"])
        if update_fields:
            update_values.append(user[0])
            cursor.execute(f"UPDATE resident SET {', '.join(update_fields)} WHERE email = %s", tuple(update_values))
        conn.commit()
        return {"success": True, "message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_my_profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


def update_user_role(conn, username: str, role: str):
    try:
        valid_roles = ["resident", "employee", "admin"]
        if role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM login WHERE username = %s", (username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        cursor.execute("UPDATE login SET user_role = %s WHERE username = %s", (role, username))
        conn.commit()
        return {"success": True, "message": f"User role updated to '{role}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_user_role error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user role")