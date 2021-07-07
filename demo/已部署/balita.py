import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class BalitaSpider(scrapy.Spider):
    name = 'balita'
    allowed_domains = ['balita.net.ph']
    start_urls = ['http://balita.net.ph/']
    website_id = 195  # 网站的id(必填)
    language_id = 2117  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(BalitaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        if re.match(r'http://balita.net.ph/$', response.url):  # 二级目录
            soup = BeautifulSoup(response.text, 'html.parser')
            for i in soup.select('ul.sub-menu > li > a'):
                url = i.get('href')
                yield scrapy.Request(url, callback=self.parse)
        if re.match(r'http://balita.net.ph/category/', response.url):
            soup = BeautifulSoup(response.text, 'html.parser')
            flag = True
            for i in soup.select('div.tablediv ~ div'):  # 每页的文章
                url = i.select_one('a').get('href')
                pub_time = Util.format_time2(i.select_one('.meta_date').text)
                if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                    yield scrapy.Request(url, callback=self.parse_item)
                else:
                    flag = False
                    self.logger.info('时间截止')
                    break
            if flag:
                try:
                    nextPage = soup.select_one('span.current ~ a ').get('href')  # 翻页
                    yield scrapy.Request(url=nextPage, callback=self.parse)
                except:
                    self.logger.info(response.url+' has no the next page.')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        category = soup.select('span.post_cat > a')[0].text.split('/')
        if len(category) == 1:
            item['category1'] = category
            item['category2'] = None
        else:
            item['category1'] = category[0]
            item['category2'] = category[1]
        item['title'] = soup.select('h1.entry_title')[0].text
        item['pub_time'] = Util.format_time2(soup.select('span.post_date')[0].text)
        item['images'] = None
        item['abstract'] = soup.select_one('p').text
        ss = ''
        for i in soup.select('p'):
            ss += i.text + r'\n'
        item['body'] = ss

        yield item
