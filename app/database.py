import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import time
from app.core.config import DB_CONFIG

logger = logging.getLogger(__name__)

def get_connection(retries: int = 3, delay: float = 1.0):
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                dbname=DB_CONFIG["DATABASE"],
                user=DB_CONFIG["USER"],
                password=DB_CONFIG["PASSWORD"],
                host=DB_CONFIG["HOST"],
                port=DB_CONFIG["PORT"],
                cursor_factory=RealDictCursor,
                sslmode='require' # Added for cloud deployments like Render
            )
            return conn
        except psycopg2.Error as e:
            logger.warning(f"DB connection attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    raise Exception("Database connection failed.")

def get_db():
    conn = get_connection()
    try:
        yield conn
    finally: 
        conn.close()