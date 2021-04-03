import pymysql
from constants import GET_SECTION_SQL, GET_MACHINE_SQL, GET_AUTO_SWITCH_SQL, \
     DB_LOGGER_MSG
from decorator.logger_decorator import BasicLogger
from reference.secret import DB_HOST, DB_USER, DB_PASSWORD
from logger.custom_logger import custom_logger


class DBHandler:
    def __init__(self):
        self.conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, charset='utf8')
        self.cursor = self.conn.cursor()

    @BasicLogger(DB_LOGGER_MSG("Sections"))
    def get_sections(self):
        self.cursor.execute(GET_SECTION_SQL)
        return self.cursor.fetchall()

    @BasicLogger(DB_LOGGER_MSG("Machines"))
    def get_machines(self):
        self.cursor.execute(GET_MACHINE_SQL)
        return self.cursor.fetchall()

    def get_auto_created(self, machine: str):
        self.cursor.execute(GET_AUTO_SWITCH_SQL(machine))
        return self.cursor.fetchall()[0][0]

    def disconnect(self):
        self.conn.close()
        custom_logger.success('Database Disconnected')
