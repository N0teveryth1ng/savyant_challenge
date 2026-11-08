import pymysql
from pymysql.cursors import DictCursor
from app import config


def create_connection():
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=DictCursor,
        autocommit=False,   # we control transactions ourselves
    )


def get_db():
    """FastAPI dependency: one connection per request, always closed."""
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()
