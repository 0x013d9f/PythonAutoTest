import pymysql


class MysqlUtil:
    def __init__(self, host='localhost', port=3306, user='root', password='root', database='py_db', charset='utf8'):
        # print('------ init class MysqlUtil ------')
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.con = None

    def __enter__(self):
        # print('------ enter class MysqlUtil ------')
        self.con = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            charset=self.charset
        ) if self.con is None else self.con
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print('------ exit class MysqlUtil ------')
        self.con.close()
        self.con = None
        return False

    def insert_many(self, table_name, filed_list, value_list):
        with self.con.cursor() as cursor:
            sql = "insert into %s (%s) values (%s)" % (
                table_name,
                ', '.join(filed_list),
                ', '.join(['%s' for i in range(len(filed_list))])
            )
            cursor.executemany(sql, tuple(value_list))
            data = cursor.fetchall()
            self.con.commit()
        return data

    def update(self, sql):
        with self.con.cursor() as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
            self.con.commit()
        return data

    def select(self, sql):
        with self.con.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def delete_all(self, table):
        self.update(f"delete from {table} where true")
