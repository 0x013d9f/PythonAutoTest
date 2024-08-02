import random
import time

from selenium.webdriver.remote.webelement import WebElement

import DBUtils
from gettestdata import GetTestData
from teststory import TestStory
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome_WD
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox_WD
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.options import PageLoadStrategy
from selenium.webdriver.common.by import By


def wait_element(driver, value, by=By.XPATH, timeout=5):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def wait_elements(driver, value, by=By.XPATH, timeout=5):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, value)))


def wait(sec):
    time.sleep(sec)


class PageOperation:

    @staticmethod
    def init_browser(
            driver_path,
            browser_path
    ) -> Chrome_WD | Firefox_WD:
        option = webdriver.ChromeOptions()
        option.binary_location = browser_path
        option.page_load_strategy = PageLoadStrategy.normal
        option.add_experimental_option('detach', True)

        driver = webdriver.Chrome(options=option, service=Service(driver_path))
        driver.maximize_window()
        return driver

    @staticmethod
    def init_database(test_story: TestStory):
        with DBUtils.MysqlUtil(database='finance') as db:
            if test_story == TestStory.LOGIN:
                pass
            if test_story == TestStory.SIGN:
                pass
            if test_story == TestStory.MANAGE_CARD:
                pass
            if test_story == TestStory.LOAN:
                pass
            if test_story == TestStory.FUNDS:
                pass
            # print(f'\t========== test story < {test_story.value} > ==========')

    def user_login(self, driver: Chrome_WD | Firefox_WD, username: str, password: str) -> None:
        driver.get('http://localhost:90/')
        driver.refresh()
        time.sleep(1)

        username_ipt = driver.find_element(By.ID, 'username')
        username_ipt.send_keys(username)
        password_ipt = driver.find_element(By.ID, 'password')
        password_ipt.send_keys(password)
        time.sleep(2)

        print(username_ipt.text, '\n', password_ipt.text)
        driver.find_element(By.ID, 'login_btn').click()

    def user_logout(self, driver: Chrome_WD | Firefox_WD) -> None:
        driver.refresh()
        wait(1)
        driver.find_element(By.XPATH, '//*[@id="topbarheader"]/nav/div/ul/li[1]').click()
        wait(1)
        driver.find_element(By.PARTIAL_LINK_TEXT, '退出登录').click()

    def user_sign(self, driver: Chrome_WD | Firefox_WD, username: str, password: str, repassword: str) -> None:
        driver.get('http://localhost:90/')
        driver.refresh()
        wait(1)

        driver.find_element(By.PARTIAL_LINK_TEXT, '还没有账号？去注册').click()
        WebDriverWait(driver, 5).until(EC.title_is('个人理财系统注册界面'))
        driver.find_element(By.ID, 'username').send_keys(username)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.ID, 'repassword').send_keys(repassword)
        wait(2)
        driver.find_element(By.ID, 'login_btn').click()
        wait(2)

    def open_page(self, driver: Chrome_WD | Firefox_WD, item_index, page_index) -> None:
        wait(2)
        item_btn_xpath = f'//*[@id="leftbaraside"]/div[2]/nav/ul/li[{item_index}]'
        item_btn = wait_element(driver, item_btn_xpath, By.XPATH)
        item_btn.click()
        time.sleep(0.5)

        page_btn_xpath = f'//*[@id="leftbaraside"]/div[2]/nav/ul/li[{item_index}]/ul/li[{page_index}]/a'
        page_btn = wait_element(driver, page_btn_xpath, By.XPATH)
        page_btn.click()
        time.sleep(0.5)

    def get_bankcard_list(self, driver: Chrome_WD | Firefox_WD) -> list:
        time.sleep(0.5)
        card_list = driver.find_elements(By.CLASS_NAME, 'col-sm-12')
        added_card_list = []
        for card in card_list:
            card_info = self.get_bankcard_info(card)
            added_card_list.append(card_info)
        return added_card_list

    """
    default get last card info and return if parameter type is WebDriver's
    :return tuple[cardID, balance, bank_name, cardType(1: debit cards, 2: credit card)]
    """
    def get_bankcard_info(self, card_el_or_webdriver: WebElement | Chrome_WD | Firefox_WD) -> tuple | tuple[str, float, str, int]:
        if not isinstance(card_el_or_webdriver, (WebElement, Chrome_WD, Firefox_WD)):
            return ()
        if isinstance(card_el_or_webdriver, WebElement):
            last_card_el = card_el_or_webdriver
        else:
            last_card_el = self.get_last_bankcard_WebElement(card_el_or_webdriver)

        wait(1)

        id = last_card_el.find_element(
            By.XPATH,
            './div/div[2]/h4[1]').get_attribute('innerHTML')[3:]
        ba = float(last_card_el.find_element(
            By.XPATH,
            './div/div[2]/h4[2]').get_attribute('innerHTML').lstrip('账户余额：').rstrip('元'))
        bank_name, card_type = last_card_el.find_element(
            By.XPATH,
            './div/div[1]/div/h4').get_attribute('innerHTML').split(' (')
        card_type = 1 if card_type[:3] == '借记卡' else 2
        return id, ba, bank_name, card_type

    def get_last_bankcard_WebElement(self, driver) -> WebElement | None:
        time.sleep(0.5)
        card_list = driver.find_elements(By.CLASS_NAME, 'col-sm-12')
        return card_list[-1] if len(card_list) > 0 else None

    def change_default_bankcard(self, driver: Chrome_WD | Firefox_WD):
        self.open_page(driver, 4, 3)
        target_card_el = driver.find_elements(By.CLASS_NAME, 'col-sm-12')[1]
        change_default_btn = target_card_el.find_element(By.CLASS_NAME, 'default_btn')
        change_default_btn.click()

    def by_financial(self, driver: Chrome_WD | Firefox_WD, page_index, pay_pwd):
        self.open_page(driver, 2, page_index)
        time.sleep(1)
        # 确定起投资金额所在栏index
        t_head_list = driver.find_elements(By.XPATH, '//thead/tr/th')
        buy_cost_index = -1
        for i, e in enumerate(t_head_list):
            if e.get_attribute('innerHTML') == '起投金额':
                buy_cost_index = i + 1
                break
        # 获取选定的投资项目WebElement并截取起投金额
        select_financial_el = driver.find_element(By.XPATH, f'//tbody/tr[1]')
        buy_cost = float(select_financial_el.find_element(By.XPATH, f'./td[{buy_cost_index}]').text.rstrip('元'))
        select_financial_el.find_element(By.XPATH, f'./td[{len(t_head_list)}]/button').click()
        time.sleep(1)
        # 输入密码确定投资
        wait_element(driver, '/html/body/div[3]/div[2]/input').send_keys(pay_pwd)
        driver.find_element(By.XPATH, '//*[@id="layui-layer1"]/div[3]/a[1]').click()
        time.sleep(2)

        return buy_cost

    def add_bankcard(self, driver: Chrome_WD | Firefox_WD, bank_name, card_type, card_number):
        add_card_xpath = '//*[@id="bankCard_add_modal_btn"]'
        bank_name_xpath = '//*[@id="cardBank_add_input"]'
        card_type_xpath = f'//*[@id="bankCardAddModal"]/div/div/div[2]/form/div[2]/div[1]/div/label[{card_type + 1}]'
        card_number_xpath = '//*[@id="cardNum_add_input"]'
        save_btn_id = 'bankCard_save_btn'

        time.sleep(0.5)
        # 点击添加银行卡
        driver.find_element(By.XPATH, add_card_xpath).click()
        time.sleep(0.5)
        # 输入银行名称
        wait_element(driver, bank_name_xpath, By.XPATH).send_keys(bank_name)
        # 选择银行卡类别
        driver.find_element(By.XPATH, card_type_xpath).click()
        time.sleep(0.5)
        # 输入银行卡号
        driver.find_element(By.XPATH, card_number_xpath).send_keys(card_number)
        time.sleep(0.5)
        # 点击保存
        driver.find_element(By.ID, save_btn_id).click()
        driver.refresh()

    def delete_last_bankcard(self, driver: Chrome_WD | Firefox_WD, isconfirm) -> None:
        card_el = self.get_last_bankcard_WebElement(driver)
        if card_el is not None:
            delete_btn = card_el.find_element(By.CSS_SELECTOR, '.btn.btn-danger.delete_btn')
            delete_btn.click()
            wait(0.5)
            _ = f'/html/body/div[2]/div[2]/div/div/div/div/div/div/div/div[4]/button[{1 if isconfirm else 2}]'
            wait_element(driver, _).click()
            driver.refresh()

    def modify_card_info(self, driver, field, value):
        card_el = self.get_last_bankcard_WebElement(driver)
        card_info = self.get_bankcard_info(card_el)
        update_btn = card_el.find_element(By.CSS_SELECTOR, '.btn.btn-primary.update_btn')
        update_btn.click()
        wait(2)

        if field == 'name':
            bank_name_input = wait_element(driver, '//*[@id="cardBank_update_input"]')
            bank_name_input.clear()
            bank_name_input.send_keys(str(card_info[-2] + value))
        elif field == 'number':
            bank_name_input = wait_element(driver, '//*[@id="cardNum_update_input"]')
            bank_name_input.clear()
            bank_name_input.send_keys(str(random.randint(10 ** (value - 1), (10 ** value) - 1)))
        elif field == 'type':
            card_type = 1 if card_info[-1] == 2 else 2
            card_type_xpath = f'//*[@id="bankCardUpdateModal"]/div/div/div[2]/form/div[2]/div[1]/div/label[{card_type}]'
            wait_element(driver, card_type_xpath).click()

        wait(2)
        driver.find_element(By.XPATH, '//*[@id="bankCard_update_btn"]').click()

    def apply_loan(self, driver, loan_money, term):
        self.open_page(driver, 3, 2)
        wait(1)
        amount_ipt = driver.find_element(By.ID, 'amount')
        term_ipt = driver.find_element(By.ID, 'term')
        submit_btn = driver.find_element(By.ID, 'submit')

        amount_ipt.send_keys(loan_money)
        term_ipt.send_keys(term)
        wait(1)
        submit_btn.click()
        wait(1)
        driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div/div/div/div/div/div/div[4]/button[1]').click()

    def audit_user_loan(self, driver, username):
        self.user_logout(driver)
        wait(1)
        self.user_login(driver, 'admin', '123456')
        self.open_page(driver, 5, 1)

        driver.find_element(By.PARTIAL_LINK_TEXT, '末页').click()
        driver.refresh()
        wait(1)

        loan_list = driver.find_elements(By.XPATH, '//tbody/tr')

        last_target_lona_el = None
        for loan_el in loan_list:
            if loan_el.find_element(By.XPATH, './td[2]').text == username:
                last_target_lona_el = loan_el

        pass_button = last_target_lona_el.find_element(By.XPATH, './td[7]/button[1]')
        pass_button.click()
        time.sleep(2)
        confirm_btn = wait_element(driver, '/html/body/div[2]/div[2]/div/div/div/div/div/div/div/div[4]/button[1]')
        confirm_btn.click()

    def check_card_isadded(self, driver, card_number, pre_card_list, balance=10000) -> bool:
        driver.refresh()
        wait(1)
        _list = self.get_bankcard_list(driver)

        if pre_card_list == _list:
            return False

        number, balance_ = _list[-1][:2]
        return card_number == number and balance_ == float(balance)

    def check_last_card_isdeleted(self, driver, pre_list) -> (bool, str):
        now_list = self.get_bankcard_list(driver)
        if pre_list == now_list:
            return False, '没有卡被删除'

        isdelete = now_list == pre_list[:-1]
        return isdelete, '最后一张卡被成功删除' if isdelete else '删除的不是最后一张卡'

    def check_prompt_info(self, driver, text):
        try:
            prompt_windows = wait_element(driver, '/html/body/div[3]/div[2]/div/div/div/div/div/div/div')
            prompt_text = prompt_windows.find_element(By.XPATH, './div[3]/div').text

            prompt_windows.find_element(By.XPATH, '.div[4]/button').click()
            time.sleep(0.5)
            driver.find_element(By.XPATH, '//*[@id="bankCardAddModal"]/div/div/div[3]/button[1]').click()
        except Exception as e:
            print('期待出现提示框，但未出现！')
            prompt_text = ''

        return prompt_text == text

    def check_card_ismodified(self, driver, pre_card_info):
        driver.refresh()
        wait(1)
        card_el = self.get_last_bankcard_WebElement(driver)
        info = self.get_bankcard_info(card_el)

        print('\n修改前信息：', pre_card_info)
        print('\n修改后信息：', info)

        if info == pre_card_info:
            return False, '卡信息没有被修改'
        else:
            return True, '卡信息被修改'

    @staticmethod
    def check_balance(pre_balance, now_balance, cost):
        if pre_balance == now_balance:
            return False, '金额没有扣减'
        if pre_balance != now_balance + cost:
            return False, '金额扣减但与预期不符'

        return True, '金额扣减成功'

    @staticmethod
    def check_loan_result(username, pre_loan_list, pre_balance, loan_money, isaudit):
        wait(2)
        now_lona_list = GetTestData.get_user_loan_list(username)
        now_balance = GetTestData.get_user_balance(username)

        isadd = len(now_lona_list) == len(pre_loan_list) + 1
        ispass = now_balance - pre_balance == loan_money

        if isaudit:
            if isadd and ispass:
                return True, '申请成功且审核通过，增加金额正常'
            if isadd and not ispass:
                return False, '申请成功但是审核未通过，金额未增加'
        else:
            if isadd and now_balance == pre_balance:
                return True, '申请成功'
            if isadd and now_balance != pre_balance:
                return False, '申请成功，但是银行卡金额异常变动'

        return False, '贷款申请未记录，申请失败'


    @staticmethod
    def compare_title(driver: Chrome_WD | Firefox_WD, pre_title: str, target_title: str, time_out_sec: int = 3) -> (
    bool, str):
        try_limit = time_out_sec
        while driver.title == pre_title and try_limit > 0:
            wait(1)
            try_limit -= 1

        now_title = driver.title

        return (True, f'当前页面<{now_title}>与期待页面<{target_title}>相同') \
            if now_title == target_title else \
            (False, f'当前页面<{now_title}>与期待页面<{target_title}>不相同')
