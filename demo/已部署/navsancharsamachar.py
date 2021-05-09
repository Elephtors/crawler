import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests
import socket

class NavsSpider(scrapy.Spider):
    name = 'navsancharsamachar'
    allowed_domains = ['navsancharsamachar.com']
    # start_urls = ['http://navsancharsamachar.com/']

    website_id = 1048  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }

    def start_requests(self):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(requests.get('http://navsancharsamachar.com/', headers=self.headers).text, 'html.parser')
        for i in soup.select('#menu-primary li'):
            meta = {'category1': i.select_one('a').text}
            yield Request(url=i.select_one('a').get('href'), meta=meta)

    def __init__(self, time=None, *args, **kwargs):
        super(NavsSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.post'):
            url = i.select_one('a').get('href')
            response.meta['title'] = i.select_one('h2 > a ').text
            response.meta['abstract'] = i.select_one('div.exceprt ').text
            response.meta['pub_time'] = Util.format_time2(i.select_one('.date').text)
            if self.time is None or Util.format_time3(Util.format_time2(i.select_one('.date').text)) >= int(self.time):
                yield Request(url, meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            try:
                nextPage = soup.find(class_='next page-numbers').get('href') if soup.find(
                    class_='next page-numbers').get('href') else None
                if nextPage:
                    yield Request(url=nextPage, meta=response.meta, callback=self.parse)
            except:
                self.logger.info('Next page no more!')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()

        item['category1'] = response.meta['category1']
        item['category2'] = None
        item['title'] = response.meta['title']
        # strtt = soup.select_one('#single-post-meta > span:nth-of-type(2)').text  # strtt 形如 '05/01/2021'
        item['pub_time'] = response.meta['pub_time']
        item['images'] = []
        ss = ''
        for p in soup.select('.post-entry p'):
            ss += p.text
            ss += '\n'
        item['body'] = ss
        item['abstract'] = response.meta['abstract']
        return item
