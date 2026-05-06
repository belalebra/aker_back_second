import pyodbc
import logging
import time
from app.core.config import DB_CONFIG

logger = logging.getLogger(__name__)

CONNECTION_STRING = (
    f"DRIVER={DB_CONFIG['DRIVER']};"
    f"SERVER={DB_CONFIG['SERVER']};"
    f"DATABASE={DB_CONFIG['DATABASE']};"
    f"Trusted_Connection={DB_CONFIG['Trusted_Connection']};"
)

def get_connection(retries: int = 3, delay: float = 1.0):
    """Create a new DB connection with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            conn = pyodbc.connect(CONNECTION_STRING, timeout=5)
            return conn
        except pyodbc.Error as e:
            logger.warning(f"DB connection attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    logger.error("All DB connection attempts failed.")
    raise Exception("Database connection failed after multiple retries.")

def get_db():
    """FastAPI dependency — yields a connection and closes it after request."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
