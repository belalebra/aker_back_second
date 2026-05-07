import jwt
import datetime
import logging
from passlib.context import CryptContext
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
blacklisted_tokens = set()

def is_token_blacklisted(token: str):
    return token in blacklisted_tokens

def blacklist_token(token: str):
    blacklisted_tokens.add(token)

def create_access_token(username: str, role: str):
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def login_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute("SELECT username, user_password, user_role FROM login WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user or not pwd_context.verify(password, user["user_password"]):
        return {"success": False, "message": "Invalid credentials"}

    token = create_access_token(user["username"], user["user_role"])
    return {"success": True, "access_token": token, "role": user["user_role"]}

def register_user(conn, username, password, email, phone=None, role="resident"):
    try:
        cursor = conn.cursor()
        hashed = pwd_context.hash(password)
        cursor.execute("""
            INSERT INTO login (username, user_password, user_role, email, phone)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, hashed, role, email, phone))
        conn.commit()
        return {"success": True, "message": "User registered"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": "Username or email already exists"}