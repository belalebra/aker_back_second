import psycopg2
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
            )
            return conn
        except psycopg2.Error as e:
            logger.warning(f"DB connection attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    logger.error("All DB connection attempts failed.")
    raise Exception("Database connection failed after multiple retries.")


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()