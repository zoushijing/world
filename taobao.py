from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from urllib.parse import quote
from pyquery import PyQuery as pq
import pymongo

#weibo_username = '微博账号'
#weibo_password = '微博密码'
url = 'https://login.taobao.com/member/login.jhtml'
#可以修改MAX_PAGE，改变爬取的页数
MAX_PAGE = 10



broswer = webdriver.Chrome()
wait = WebDriverWait(broswer, 10)
#可以修改KEYWORD来修改爬取的商品名称
KEYWORD = 'iPad'
MONGO_URL = 'localhost'
MONGO_DB = 'taobao'
MONGO_COLLECTION = 'products'
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
broswer.get(url)

def index_page(page):
    """
    抓取索引页
    :param page: 页码
    """
    print('正在爬取第', page, '页')
    try:
        url = 'https://s.taobao.com/search?q=' + quote(KEYWORD)
        broswer.get(url)
        if page > 1:
            input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager div.form > input')))
            submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager div.form > span.btn.J_Submit')))
            input.clear()
            input.send_keys(page)
            submit.click()
        #等待跳转成功
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager li.item.active > span'),
                str(page)))
        #等待商品加载出来
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.m-itemlist .items .item')))
        get_products()
    except TimeoutException:
        index_page(page)

def get_products():
    """
    提取商品数据
    """
    html = broswer.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('data-src'),
            'prince': item.find('.prince').text(),
            'deal': item.find('.deal-cnt').text(),
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
            }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    """
    保存到MongoDB
    :param result: 结果
    """
    try:
        if db[MONGO_COLLECTION].insert(result):
            print('存储到MongoDB成功')
    except Exception:
        print('存储到MongoDB失败')


def auto_login():
    # 打开网页
    # 等待 密码登录选项 出现
    password_login = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.qrcode-login > .login-links > .forget-pwd')))
    password_login.click()

    # 等待 微博登录选项 出现
    weibo_login = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.weibo-login')))
    weibo_login.click()

    # 等待 微博账号 出现
    weibo_user = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.username > .W_input')))
    weibo_user.send_keys(weibo_username)

    # 等待 微博密码 出现
    weibo_pwd = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.password > .W_input')))
    weibo_pwd.send_keys(weibo_password)

    # 等待 登录按钮 出现
    submit = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.btn_tip > a > span')))
    submit.click()

    # 直到获取到淘宝会员昵称才能确定是登录成功
    taobao_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                  '.site-nav-bd > ul.site-nav-bd-l > li#J_SiteNavLogin > div.site-nav-menu-hd > div.site-nav-user > a.site-nav-login-info-nick ')))
    # 输出淘宝昵称
    print("登陆成功" + taobao_name.text)
   
def main():
    """
    遍历每一页
    """
    auto_login()
    for i in range(1, MAX_PAGE + 1):
        index_page(i)

if __name__ == '__main__':
    main()

