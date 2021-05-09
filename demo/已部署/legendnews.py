
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class LegendnewsSpider(scrapy.Spider):
    name = 'legendnews'
    allowed_domains = ['legendnews.in']
    website_id = 1051  # 网站的id(必填)
    start_urls = ['http://legendnews.in/']
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(LegendnewsSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#menu-primary-menu > li > a'):  # 网站头部的目录
            meta = {'category1': i.text, 'category2': None}
            yield Request(url=i.get('href'), meta=meta, callback=self.parse_essay)  # 一级目录给parse_essay
            for j in i.select('ul > li > a'):
                meta['category2'] = j.text
                yield Request(url=j.get('href'), meta=meta, callback=self.parse_essay)

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('article '):
            pub_time = i.select_one('.updated').get('datetime').split('T')[0] + ' ' + \
                       i.select_one('.updated').get('datetime').split('T')[1].split('+')[0]
            if self.time is None or Util.format_time3(pub_time) >= int(self.time):  # 未截止，True
                response.meta['title'] = i.select_one('a').get('title')
                response.meta['abstract'] = i.select_one('p').text
                response.meta['images'] = [i.select_one('img').get('src')]
                response.meta['pub_time'] = pub_time
                yield Request(url=i.select_one('a').get('href'), meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            nextPage = soup.select_one('.previous a').get('href')
            yield Request(nextPage, meta=response.meta, callback=self.parse)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = response.meta['abstract']
        item['images'] = response.meta['images']
        item['category2'] = response.meta['category2']
        item['body'] = soup.find(class_='entry-content clearfix').text
        item['pub_time'] = response.meta['pub_time']
        return item