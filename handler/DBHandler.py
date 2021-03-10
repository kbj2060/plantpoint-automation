import pymysql
import constants


class DBHandler:
    def __init__(self):
        self.host = constants.DB_HOST
        self.user = constants.DB_USER
        self.password = constants.DB_PASSWORD
        self.conn = pymysql.connect(host=self.host, user=self.user, password=self.password, charset='utf8')
        self.cursor = self.conn.cursor()

    def get_sections(self):
        self.cursor.execute(constants.GET_SECTION_SQL)
        return self.cursor.fetchall()


db = DBHandler()
print(db.get_sections())
