
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#将爬虫类名和name字段改成对应的网站名
class DemoSpider(scrapy.Spider):
    name = 'demo'
    website_id = -1 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['www.example.com']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_xxx',
        'password': 'dg_xxx',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(DemoSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        pass