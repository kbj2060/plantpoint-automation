import pymysql
from constants import DB_HOST, DB_USER, DB_PASSWORD, GET_SECTION_SQL, GET_MACHINE_SQL, GET_AUTO_SWITCH_SQL


class DBHandler:
    def __init__(self):
        self.host = DB_HOST
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.conn = pymysql.connect(host=self.host, user=self.user, password=self.password, charset='utf8')
        self.cursor = self.conn.cursor()

    def get_sections(self):
        self.cursor.execute(GET_SECTION_SQL)
        return self.cursor.fetchall()

    def get_machines(self):
        self.cursor.execute(GET_MACHINE_SQL)
        return self.cursor.fetchall()

    def get_auto_created(self, machine: str):
        self.cursor.execute(GET_AUTO_SWITCH_SQL(machine))
        return self.cursor.fetchall()[0][0]

    def disconnect(self):
        self.conn.close()
