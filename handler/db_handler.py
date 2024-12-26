from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
from constants import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from decorator.logger_decorator import BasicLogger
from logger.custom_logger import custom_logger


class DBHandler:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)
        custom_logger.success('Database Connected')

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            custom_logger.error(f'Database error: {str(e)}')
            raise

    def get_devices(self):
        query = """
            SELECT id, name, status 
            FROM device 
            ORDER BY id
        """
        return self.execute_query(query)

    def get_automation_by_device(self, device_id):
        query = """
            SELECT category, settings, active 
            FROM automations 
            WHERE device_id = %s
        """
        return self.execute_query(query, (device_id,))

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            custom_logger.success('Database Disconnected')
