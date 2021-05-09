
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class MediakhabarSpider(scrapy.Spider): 
    name = 'mediakhabar'
    allowed_domains = ['mediakhabar.com']
    start_urls = ['http://mediakhabar.com/']
    website_id = 1062  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(MediakhabarSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response): # 有三级目录，难点在于进入目录，翻页和parseitem都不难
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#td-header-menu ul > li')[1:]:
            meta = {'category1': i.select_one('a').text, 'category2': None}
            yield Request(url=i.select_one('a').get('href'), meta=meta, callback=self.parse_essay)  # 一级目录给parse_essay
            try:
                for j in i.select('ul>li>a'):
                    meta['category2']= j.text
                    yield Request(url=j.get('href'), meta=meta, callback=self.parse_essay)
                    try:
                        for t in j.select('ul>li>a'):
                            yield Request(url=t.get('href'), meta=meta, callback=self.parse_essay)
                    except:
                        self.logger.info('No more category3')
                        continue
            except:
                self.logger.info('No more category2!')
                continue

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.td-block-span6 '):
            pub_time = i.select_one('.td-post-date time').get('datetime').split('T')[0]+' '+i.select_one('.td-post-date time').get('datetime').split('T')[1].split('+')[0]
            response.meta['title'] = i.select_one('a').get('title')
            response.meta['pub_time'] = pub_time
            response.meta['images'] = [i.select_one('a img').get('src')]
            if self.time is None or Util.format_time3(pub_time) >= int(self.time):
                yield Request(url=i.select_one('a').get('href'), meta=response.meta,
                              callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            try:
                nextPage = soup.select_one('.current ~ a').get('href', 'Next page no more')
                yield Request(nextPage, meta=response.meta, callback=self.parse_essay)
            except Exception:
                pass

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = soup.select_one('.td-post-content > p').text
        ss = ''
        for i in soup.select('.td-post-content > p'):
            ss += i.text + '\n'
        item['body'] = ss
        item['images'] = response.meta['images']
        item['category2'] = response.meta['category2']
        item['pub_time'] = response.meta['pub_time']
        # self.logger.info('item item item item item item item item item item item item')
        return item
