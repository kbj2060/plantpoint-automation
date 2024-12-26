import psycopg2
from psycopg2.extras import DictCursor
from constants import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from logger.custom_logger import custom_logger

class Database:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
            custom_logger.success("Database Connected")
        except Exception as e:
            custom_logger.error(f"Database Connection Failed: {str(e)}")
            raise

    def disconnect(self):
        """데이터베이스 연결 종료"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            custom_logger.success("Database Disconnected") 