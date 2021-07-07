import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import socket

class JanoSpider(scrapy.Spider):
    name = 'janoduniya'
    allowed_domains = ['janoduniya.tv']
    #start_urls = ['http://janoduniya.tv/']
    website_id = 1057  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def start_requests(self):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(requests.get('http://janoduniya.tv/').text, 'html.parser')
        for i in soup.select('#primary-menu a')[:-1]:
            meta = {'category1': i.text}
            yield Request(url=i.get('href'), meta=meta)

    def __init__(self, time=None, *args, **kwargs):
        super(JanoSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('article'):
            pub_time = Util.format_time2(soup.select_one('.updated').text)
            response.meta['title'] = soup.select_one('h2.entry-title a').text
            response.meta['pub_time'] = pub_time
            if self.time is None or Util.format_time3(pub_time) >= int(self.time):
                yield Request(url=i.select_one('a').get('href'), meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
        if flag:
            try:
                nextPage = soup.select_one('.nav-previous a').get('href')
                yield Request(nextPage, meta=response.meta, callback=self.parse)
            except:
                self.logger.info('Next page no more')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = soup.select_one('.entry-content p').text
        ss = ''
        for i in soup.select('.entry-content p'):
            ss += i.text
        item['body'] = ss
        item['images'] = [i.get('src') for i in soup.select('.np-article-thumb img')]
        item['category2'] = None
        item['pub_time'] = response.meta['pub_time']
        self.logger.info('item item item item item item item item item item item item')
        return item
