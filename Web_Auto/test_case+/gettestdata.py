import random

import yaml
from faker import Faker

import DBUtils
from teststory import TestStory

class GetTestData:
    @staticmethod
    def read_file():
        with open(
                file='./test_case.yaml',
                mode='r',
                encoding='utf-8'
        ) as data:
            result = yaml.load(data.read(), Loader=yaml.FullLoader)
        return result

    @staticmethod
    def get_test_case_data(story: TestStory):
        data = GetTestData.read_file()
        return data[story.value + '_case']

    @staticmethod
    def get_user_balance(username):
        with DBUtils.MysqlUtil(database='finance') as db:
            try:
                balance = float(db.select(f"""
                    select balance from bankcard where userId = (
                        select id from user where username like '{username}'
                    ) and defaultl = 1
                    """)[0][0])
            except IndexError as e:
                balance = -1

            return balance

    @staticmethod
    def get_user_loan_list(username):
        with DBUtils.MysqlUtil(database='finance') as db:
            try:
                sql = f"""
            select id, userId, adminId, startTime, amount, term, rate, applyStatus, loanStatus from loan where userId = (
                select id from user where username like '{username}'
            )
            """
                return db.select(sql)
            except Exception as e:
                return ()

    @staticmethod
    def init_data(story):
        fake = Faker(locale='zh-CN')
        with DBUtils.MysqlUtil(database='finance') as db:
            # 清空用户卡信息
            db.update("""
        delete from bankcard where userId in (
            select id from user where username like ('lisi_')
        )
        """)
            # 清空用户账号信息
            db.update("delete from user where username like ('lisi_')")

            if story == TestStory.LOGIN:
                db.update("insert into user(username, password) values ('lisi2', '123!@#$%^%&456')")

            if story == TestStory.SIGN:
                db.update("delete from user where username like '%wangwu%'")

            if story == TestStory.MANAGE_CARD:
                db.update("delete from bankcard where id > 3")

            if story == TestStory.FINANCIAL or story == TestStory.LOAN:
                # 清空用户卡信息
                db.update("""
        delete from bankcard where userId in (
            select id from user where username like ('lisi_')
        )
        """)

                # 清空用户账号信息
                db.update("delete from user where username like ('lisi_')")

                # 获取最大ID
                user_max = db.select('select max(id) from user')[0][0]
                card_max = db.select('select max(id) from bankcard')[0][0]

                # 添加用户账号
                # [支付密码, 卡数量, 余额]
                card_info = [
                    ['666666', 1, 100000],
                    ['666666', 1, 0],
                    ['666666', 0],
                    ['', 1, 100000],
                    ['666666', 3, 100000],
                ]
                for i, e in enumerate(range(3, 8)):
                    db.update(f"""
                        insert into user(id, username, realname, password, idcard, phone, email, paypwd, status, reputation) values (
                            '{user_max + i + 1}',
                            'lisi{e}',
                            '李四{e}',
                            'e10adc3949ba59abbe56e057f20f883e',
                            '{fake.ssn()}',
                            '{fake.phone_number()}',
                            '{fake.email()[-20:]}',
                            {card_info[i][0] if card_info[i][0] != "" else "NULL"},
                            '1',
                            '良好'
                        )""")

                    for j in range(card_info[i][1]):
                        db.update(f"""
                        insert into bankcard(id, cardBank, type, cardNum, userId, balance, defaultl) VALUES (
                            '{card_max + i + j + 1}',
                            '中国建设银行',
                            '1',
                            '{random.randint(10 ** 15, 10 ** 16 - 1)}',
                            '{user_max + i + 1}',
                            '{card_info[i][2]}',
                            '{1 if j == 0 else 0}'
                        )""")


if __name__ == '__main__':
    reader = GetTestData()
    print(GetTestData.get_test_case_data(TestStory.FINANCIAL)['case_1'])
