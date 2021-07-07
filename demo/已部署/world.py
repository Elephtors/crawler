import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class WorldSpider(scrapy.Spider):
    name = 'world'
    allowed_domains = ['worldnews.net.ph']
    start_urls = ['https://worldnews.net.ph/']
    website_id = 183  # 网站的id(必填)
    language_id = 2266  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(WorldSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        m = {}
        for i in soup.select('#menu-main-menu>li> a')[1:-1]:
            url = i.get('href')
            m['category1'] = i.get('title')
            yield scrapy.Request(url, callback=self.parse_menu, meta=m)

    def parse_menu(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('article > div.content '):  # 每页的文章
            url = i.select_one('a').get('href')
            if self.time == None or Util.format_time3(i.select_one('time').text+' 00:00:00') >= int(self.time):
                yield scrapy.Request(url, meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            try:
                yield scrapy.Request(soup.select('.pagination > li a')[-1].attrs['href'], meta=response.meta, callback=self.parse_menu)
            except Exception:
                pass

    # def parse_essay(self, response):
    #     soup = bs(response.text, 'html.parser')
    #     for i in soup.select('article > div.content a'):  # 每页的文章
    #         url = i.get('href')
    #         yield scrapy.Request(url, meta=response.meta, callback=self.parse_item)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = None
        item['title'] = soup.select_one('h1.post-title.item.fn').text
        item['pub_time'] = soup.select('time.value-title')[0].text + ' 00:00:00'
        item['images'] = None
        item['abstract'] = soup.select('article > div > div >div >p')[0].text
        ss = ''
        for i in soup.select('article > div > div >div >p'):
            ss += i.text + r'\n'
        item['body'] = ss
        return item
