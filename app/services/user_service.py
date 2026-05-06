import logging
from pyodbc import Connection
from fastapi import HTTPException
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Get All Users (Admin) ─────────────────────────────────────
def get_all_users(conn: Connection):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                l.username, l.email, l.user_role, l.phone,
                r.f_name, r.l_name,
                r.resident_phone_num AS resident_phone,
                r.area, r.apartment_number, r.unit_number,
                r.joining_date, r.total_requests
            FROM Login l
            LEFT JOIN Resident r ON r.email = l.email
            ORDER BY l.username
        """)
        rows = cursor.fetchall()
        return [
            {
                "username":         r.username,
                "email":            r.email,
                "role":             r.user_role,
                "phone":            r.phone,
                "f_name":           r.f_name,
                "l_name":           r.l_name,
                "area":             r.area,
                "apartment_number": r.apartment_number,
                "unit_number":      r.unit_number,
                "joining_date":     str(r.joining_date) if r.joining_date else None,
                "total_requests":   r.total_requests,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_all_users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


# ── Update My Profile ─────────────────────────────────────────
def update_my_profile(conn: Connection, username: str, data: dict):
    try:
        cursor = conn.cursor()

        # Update Login table
        if data.get("phone"):
            cursor.execute(
                "UPDATE Login SET phone = ? WHERE username = ?",
                data["phone"], username
            )

        # Update password if provided
        if data.get("new_password"):
            hashed = pwd_context.hash(data["new_password"])
            cursor.execute(
                "UPDATE Login SET user_password = ? WHERE username = ?",
                hashed, username
            )

        # Update Resident table
        cursor.execute("SELECT email FROM Login WHERE username = ?", username)
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_fields = []
        update_values = []

        if data.get("f_name"):
            update_fields.append("f_name = ?")
            update_values.append(data["f_name"])
        if data.get("l_name"):
            update_fields.append("l_name = ?")
            update_values.append(data["l_name"])
        if data.get("phone"):
            update_fields.append("resident_phone_num = ?")
            update_values.append(data["phone"])

        if update_fields:
            update_values.append(user.email)
            cursor.execute(
                f"UPDATE Resident SET {', '.join(update_fields)} WHERE email = ?",
                *update_values
            )

        conn.commit()
        logger.info(f"Profile updated for: {username}")
        return {"success": True, "message": "Profile updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_my_profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


# ── Update User Role (Admin) ──────────────────────────────────
def update_user_role(conn: Connection, username: str, role: str):
    try:
        valid_roles = ["resident", "employee", "admin"]
        if role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )

        cursor = conn.cursor()
        cursor.execute("SELECT username FROM Login WHERE username = ?", username)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute(
            "UPDATE Login SET user_role = ? WHERE username = ?",
            role, username
        )
        conn.commit()

        logger.info(f"Role updated for {username} to {role}")
        return {"success": True, "message": f"User role updated to '{role}'"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_user_role error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user role")
