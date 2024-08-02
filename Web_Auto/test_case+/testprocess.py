import pytest
from itertools import product
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome_WD
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox_WD

from gettestdata import GetTestData
from pageoperation import PageOperation
from pageoperation import TestStory


@pytest.fixture(scope='class', autouse=True)
def browser_handler(request):
    print('\n\t++++++++++++ fixture init browser start ++++++++++++')
    driver = None
    if request.param == 'firefox':
        driver = PageOperation.init_browser(
            driver_path=r'D:\Programs\Mozilla Firefox\geckodriver.exe',
            browser_path=r'D:\Programs\Mozilla Firefox\firefox.exe',
        )
    # default driver chrome
    if driver is None:
        driver = PageOperation.init_browser(
            driver_path=r'D:\Programs\chromedriver-win64\chromedriver.exe',
            browser_path=r'D:\Programs\chromedriver-win64\chrome-win64\chrome.exe',
        )

    print(f'\n\t-------- browser: {request.param} --------')
    yield driver
    driver.close()
    print('\n\t++++++++++++ fixture init browser end ++++++++++++')


@pytest.fixture(scope='class', autouse=True)
def init_database(request):
    print('\n\t============== fixture init_database start ==============')
    print(f'\n\t-------- database init story: {request.param} --------')
    GetTestData.init_data(request.param[0])
    yield
    print('\n\t============== fixture init_database end ==============')


@pytest.fixture(scope='function')
def default_login(request, browser_handler):
    # print('\t============== fixture default login start ==============')
    username, password = request.param
    PageOperation().user_login(browser_handler, username, password)
    # print('\t============== fixture default login yield and end ==============')
    yield browser_handler


@pytest.fixture(scope='function')
def return_user_login(request, browser_handler, init_database):
    # print('\t============== fixture default login start ==============')
    username, password = request.param
    PageOperation().user_login(browser_handler, username, password)
    # print('\t============== fixture default login yield and end ==============')
    yield browser_handler, username


@pytest.mark.parametrize('browser_handler, init_database',
                         zip(['chrome', 'firefox'], product([TestStory.SIGN], range(2))), indirect=True)
class TestLogin(PageOperation):
    @pytest.mark.parametrize(
        "username, password, assert_title, islogin",
        GetTestData.get_test_case_data(TestStory.LOGIN)
    )
    def test_login(self, browser_handler: Chrome_WD | Firefox_WD, username, password, assert_title, islogin):
        driver = browser_handler
        pre_title = driver.title
        self.user_login(driver, username, password)
        result, tips = self.compare_title(driver, pre_title, assert_title)
        if islogin:
            self.user_logout(driver)
        print(tips)
        assert result


@pytest.mark.parametrize('browser_handler, init_database',
                         zip(['chrome', 'firefox'], product([TestStory.SIGN], range(2))), indirect=True)
class TestSign(PageOperation):
    @pytest.mark.parametrize(
        "username, password, repassword, target_title",
        GetTestData.get_test_case_data(TestStory.SIGN)
    )
    def test_sign(self, browser_handler: Chrome_WD | Firefox_WD, username, password, repassword, target_title):
        driver = browser_handler
        pre_title = driver.title
        self.user_sign(driver, username, password, repassword)
        result, tips = self.compare_title(driver, pre_title, target_title)

        print(tips)
        assert result


@pytest.mark.parametrize('browser_handler, init_database',
                         zip(['chrome', 'firefox'], product([TestStory.MANAGE_CARD], range(2))), indirect=True)
@pytest.mark.parametrize('default_login', [('lisi', '123456')], indirect=True)
class TestManageCard(PageOperation):
    @pytest.mark.parametrize(
        "bank_name, card_type, card_number, isadded",
        GetTestData.get_test_case_data(TestStory.MANAGE_CARD)['add']
    )
    def test_manage_card_add(self, default_login: Chrome_WD | Firefox_WD, bank_name, card_type, card_number, isadded):
        driver = default_login
        self.open_page(driver, 4, 3)
        pre_list = self.get_bankcard_list(driver)
        self.add_bankcard(driver, bank_name, card_type, card_number)

        prompt = self.check_prompt_info(driver, '银行卡新增失败！') if not isadded else True
        result = self.check_card_isadded(driver, card_number, pre_list)

        assert result == isadded
        assert prompt

    @pytest.mark.parametrize("isconfirm", GetTestData.get_test_case_data(TestStory.MANAGE_CARD)['delete'])
    def test_manage_card_delete(self, default_login: Chrome_WD | Firefox_WD, isconfirm, init_database):
        # 初始化并登录
        driver = default_login
        # 打开银行卡管理界面
        self.open_page(driver, 4, 3)
        # 获取删除前的卡包信息
        pre_list = self.get_bankcard_list(driver)
        # 删除最后一张银行卡
        self.delete_last_bankcard(driver, isconfirm)
        # 检查银行卡是否被删除
        result, tips = self.check_last_card_isdeleted(driver, pre_list)

        print(tips)

        assert result == isconfirm

    @pytest.mark.parametrize('field, value, ismodified',
                             GetTestData.get_test_case_data(TestStory.MANAGE_CARD)['modify'])
    def test_manage_card_modify(self, default_login, field, value, ismodified):
        driver = default_login
        self.open_page(driver, 4, 3)
        last_card_el = self.get_last_bankcard_WebElement(driver)
        pre_last_card_info = self.get_bankcard_info(last_card_el)
        self.modify_card_info(driver, field, value)
        result, tips = self.check_card_ismodified(driver, pre_last_card_info)

        print(tips)
        assert result == ismodified


@pytest.mark.parametrize('browser_handler, init_database',
                         zip(['chrome', 'firefox'], product([TestStory.FINANCIAL], range(2))), indirect=True)
class TestFinancial(PageOperation):
    @pytest.mark.parametrize('return_user_login, pay_pwd, text, isbuy',
                             GetTestData.get_test_case_data(TestStory.FINANCIAL)['case_1'],
                             indirect=['return_user_login'])
    def test_financial_change(self, return_user_login, pay_pwd, text, isbuy):
        driver, username = return_user_login
        pre_balance = GetTestData.get_user_balance(username)
        print(pre_balance)
        cost = self.by_financial(driver, 1, pay_pwd)
        now_balance = GetTestData.get_user_balance(username)
        print(now_balance)
        result, tips = self.check_balance(pre_balance, now_balance, cost)

        print(tips)
        assert result == isbuy

    @pytest.mark.parametrize('return_user_login, pay_pwd, text, isbuy',
                             GetTestData.get_test_case_data(TestStory.FINANCIAL)['case_1'],
                             indirect=['return_user_login'])
    def test_financial_term(self, return_user_login, pay_pwd, text, isbuy):
        driver, username = return_user_login
        pre_balance = GetTestData.get_user_balance(username)
        print(pre_balance)
        cost = self.by_financial(driver, 2, pay_pwd)
        now_balance = GetTestData.get_user_balance(username)
        print(now_balance)
        result, tips = self.check_balance(pre_balance, now_balance, cost)

        print(tips)
        assert result == isbuy

    @pytest.mark.parametrize('return_user_login, pay_pwd, text, isbuy',
                             GetTestData.get_test_case_data(TestStory.FINANCIAL)['case_1'],
                             indirect=['return_user_login'])
    def test_financial_fund(self, return_user_login, pay_pwd, text, isbuy):
        driver, username = return_user_login
        pre_balance = GetTestData.get_user_balance(username)
        print(pre_balance)
        cost = self.by_financial(driver, 3, pay_pwd)
        now_balance = GetTestData.get_user_balance(username)
        print(now_balance)
        result, tips = self.check_balance(pre_balance, now_balance, cost)

        print(tips)
        assert result == isbuy

    @pytest.mark.parametrize('return_user_login, pay_pwd, ischange, isbuy',
                             GetTestData.get_test_case_data(TestStory.FINANCIAL)['case_2'],
                             indirect=['return_user_login'])
    def test_financial_bank_card(self, return_user_login, pay_pwd, ischange, isbuy):
        driver, username = return_user_login
        if ischange:
            self.change_default_bankcard(driver)

        pre_balance = GetTestData.get_user_balance(username)
        cost = self.by_financial(driver, 3, pay_pwd)
        now_balance = GetTestData.get_user_balance(username)
        print(now_balance)
        result, tips = self.check_balance(pre_balance, now_balance, cost)

        print(tips)
        assert result == isbuy


@pytest.mark.parametrize('browser_handler, init_database',
                         zip(['chrome', 'firefox'], product([TestStory.LOAN], range(2))), indirect=True)
class TestLoan(PageOperation):
    @pytest.mark.parametrize('return_user_login, loan_money, term, isaudit, isloan',
                             GetTestData.get_test_case_data(TestStory.LOAN), indirect=['return_user_login'])
    def test_loan(self, return_user_login, loan_money, term, isaudit, isloan):
        driver, username = return_user_login
        pre_loan_list = GetTestData.get_user_loan_list(username)
        pre_balance = GetTestData.get_user_balance(username)
        self.apply_loan(driver, loan_money, term)
        if isaudit:
            self.audit_user_loan(driver, username)
        result, tips = self.check_loan_result(username, pre_loan_list, pre_balance, loan_money, isaudit)

        print(tips)
        assert result == isloan
        assert True
