import random
import openpyxl
from faker import Faker


def get_site():
    return ['zh_CN', 'en_US', 'ru_RU', 'sv_SE']


if __name__ == '__main__':
    fake = Faker(get_site())

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(['name', 'site', 'email', 'phoneNumber'])

    for e in range(100):
        _ = fake[random.choice(get_site())]
        worksheet.append([_.name(), _.address(), _.email(domain='git.cn'), _.phone_number()])

    workbook.save('./faker_generate.xlsx')
    workbook.close()
