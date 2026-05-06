import jwt
import logging
import datetime
import secrets
from passlib.context import CryptContext
from pyodbc import Connection
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Token Blacklist ───────────────────────────────────────────
blacklisted_tokens: set = set()

def blacklist_token(token: str):
    blacklisted_tokens.add(token)

def is_token_blacklisted(token: str) -> bool:
    return token in blacklisted_tokens

# ── Rate Limiting (in-memory) ─────────────────────────────────
login_attempts: dict = {}  # {username: {"count": int, "last_attempt": datetime}}
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def check_rate_limit(username: str):
    now = datetime.datetime.utcnow()
    record = login_attempts.get(username)

    if record:
        locked_since = record["last_attempt"]
        if record["count"] >= MAX_ATTEMPTS:
            diff = (now - locked_since).total_seconds() / 60
            if diff < LOCKOUT_MINUTES:
                remaining = int(LOCKOUT_MINUTES - diff)
                raise Exception(f"Account locked. Try again in {remaining} minutes.")
            else:
                login_attempts[username] = {"count": 0, "last_attempt": now}

def record_failed_attempt(username: str):
    now = datetime.datetime.utcnow()
    record = login_attempts.get(username, {"count": 0, "last_attempt": now})
    record["count"] += 1
    record["last_attempt"] = now
    login_attempts[username] = record

def reset_attempts(username: str):
    login_attempts.pop(username, None)


# ── Token Creation ────────────────────────────────────────────
def create_access_token(username: str, role: str) -> str:
    payload = {
        "username": username,
        "role": role,
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(username: str) -> str:
    payload = {
        "username": username,
        "type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Audit Log ─────────────────────────────────────────────────
def log_audit(conn: Connection, action: str, username: str, details: str = ""):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Audit_Log')
            CREATE TABLE Audit_Log (
                id         INT PRIMARY KEY IDENTITY(1,1),
                action     VARCHAR(100),
                username   VARCHAR(100),
                details    VARCHAR(500),
                created_at DATETIME DEFAULT GETDATE()
            )
        """)
        cursor.execute(
            "INSERT INTO Audit_Log (action, username, details) VALUES (?, ?, ?)",
            action, username, details
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Audit log error: {e}")


# ── User Helpers ──────────────────────────────────────────────
def get_user_by_username(conn: Connection, username: str):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Login WHERE username = ?", username)
    return cursor.fetchone()

def get_user_by_email(conn: Connection, email: str):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Login WHERE email = ?", email)
    return cursor.fetchone()


# ── Login ─────────────────────────────────────────────────────
def login_user(conn: Connection, username: str, password: str):
    try:
        check_rate_limit(username)

        user = get_user_by_username(conn, username)
        if not user:
            record_failed_attempt(username)
            log_audit(conn, "LOGIN_FAILED", username, "User not found")
            return {"success": False, "message": "Invalid username or password"}

        password_match = False
        if user.user_password.startswith("$2b$"):
            password_match = pwd_context.verify(password, user.user_password)
        else:
            password_match = (password == user.user_password)

        if not password_match:
            record_failed_attempt(username)
            log_audit(conn, "LOGIN_FAILED", username, "Wrong password")
            logger.warning(f"Wrong password: {username}")
            return {"success": False, "message": "Invalid username or password"}

        reset_attempts(username)
        access_token  = create_access_token(username, user.user_role)
        refresh_token = create_refresh_token(username)

        log_audit(conn, "LOGIN_SUCCESS", username, f"Role: {user.user_role}")
        logger.info(f"Successful login: {username}")

        return {
            "success": True,
            "message": "Login successful",
            "role": user.user_role,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    except Exception as e:
        if "locked" in str(e):
            return {"success": False, "message": str(e)}
        logger.error(f"Login error: {e}")
        raise


# ── Register ──────────────────────────────────────────────────
def register_user(conn: Connection, username: str, password: str, email: str, phone: str = None, role: str = "resident"):
    try:
        if get_user_by_username(conn, username):
            return {"success": False, "message": "Username already exists"}

        if get_user_by_email(conn, email):
            return {"success": False, "message": "Email already exists"}

        hashed = pwd_context.hash(password)
        cursor = conn.cursor()
        cursor.execute(
             "INSERT INTO Login (username, user_password, user_role, email, phone) VALUES (?, ?, ?, ?, ?)",
             username, hashed, role, email, phone
        )
        conn.commit()

        log_audit(conn, "REGISTER", username, f"Role: {role}")
        logger.info(f"New {role} registered: {username}")
        return {"success": True, "message": f"{role.capitalize()} registered successfully"}

    except Exception as e:
        logger.error(f"Register error: {e}")
        raise


# ── Refresh Token ─────────────────────────────────────────────
def refresh_access_token(conn: Connection, refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return {"success": False, "message": "Invalid token type"}

        username = payload.get("username")
        user = get_user_by_username(conn, username)
        if not user:
            return {"success": False, "message": "User not found"}

        new_access_token = create_access_token(username, user.user_role)
        log_audit(conn, "TOKEN_REFRESH", username, "")
        return {"success": True, "access_token": new_access_token}

    except jwt.ExpiredSignatureError:
        return {"success": False, "message": "Refresh token expired, please login again"}
    except jwt.InvalidTokenError:
        return {"success": False, "message": "Invalid refresh token"}


# ── Password Reset ────────────────────────────────────────────
reset_tokens: dict = {}  # {email: {"token": str, "exp": datetime}}

def request_password_reset(conn: Connection, email: str):
    try:
        user = get_user_by_email(conn, email)
        if not user:
            return {"success": False, "message": "Email not found"}

        token = secrets.token_urlsafe(32)
        exp   = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        reset_tokens[email] = {"token": token, "exp": exp}

        log_audit(conn, "PASSWORD_RESET_REQUEST", user.username, f"Email: {email}")
        logger.info(f"Password reset requested for: {email}")

        # In production: send token via email/SMS
        return {"success": True, "message": "Reset token generated", "reset_token": token}

    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise


def confirm_password_reset(conn: Connection, email: str, token: str, new_password: str):
    try:
        record = reset_tokens.get(email)
        if not record:
            return {"success": False, "message": "No reset request found"}

        if record["token"] != token:
            return {"success": False, "message": "Invalid reset token"}

        if datetime.datetime.utcnow() > record["exp"]:
            reset_tokens.pop(email, None)
            return {"success": False, "message": "Reset token expired"}

        hashed = pwd_context.hash(new_password)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Login SET user_password = ? WHERE email = ?",
            hashed, email
        )
        conn.commit()
        reset_tokens.pop(email, None)

        user = get_user_by_email(conn, email)
        log_audit(conn, "PASSWORD_RESET_SUCCESS", user.username if user else email, "")
        return {"success": True, "message": "Password reset successfully"}

    except Exception as e:
        logger.error(f"Password reset confirm error: {e}")
        raise
