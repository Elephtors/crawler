import json
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class RaftaarSpider(scrapy.Spider):
    name = 'raftaar'
    allowed_domains = ['news.raftaar.in']
    start_urls = ['https://news.raftaar.in/']

    website_id = 1052  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(RaftaarSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    url_api = 'https://news.raftaar.in/api/v1/collections/{}?item-type=story&offset={}&limit=20'
    #  第一个花括号目录   offset从首项20，以20递增，limit,一次拿几个item

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('div.header-one-m__default-menu__1eHwj>ul>li'):
            meta = {'category1': i.select_one('a').text, 'category2': None,
                    'category': i.select_one('a').get('href').split('/')[-1],
                    'offset': 20}    # 一级目录直接取url最后的单词
            url = self.url_api.format(meta['category'], str(meta['offset']))
            yield Request(url=url, meta=meta, callback=self.parse_essay)
            for j in i.select('ul>li'):
                meta['category2'] = j.select_one('a').text
                # 二级目录单词加在一级目录之前，以'-'相连
                if re.match('https://news.raftaar.in', j.select_one('a').get('href')):
                    temp = meta['category']
                    meta['category'] = j.select_one('a').get('href').split('/')[-1] + '-' +temp  # 更新为二级目录
                    url = self.url_api.format(meta['category'], str(meta['offset']))
                    yield Request(url=url, meta=meta, callback=self.parse_essay)
                    meta['category'] = temp   # 恢复原来一级目录
                else:
                    self.logger.info('Invalid URL: '+j.select_one('a').get('href'))

    def parse_essay(self, response):
        js = json.loads(response.text)
        flag = True
        for i in js['items']:
            pub_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(i['story']['last-published-at'] / 1000))
            if self.time == None or (Util.format_time3(pub_time)) >= int(self.time):
                response.meta['title'] = i['item']['headline'][0]
                response.meta['pub_time'] = pub_time
                news_url = 'https://news.raftaar.in/'+i['story']['slug']
                yield Request(url=news_url, callback=self.parse_item, meta=response.meta)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            response.meta['offset'] += 20
            if response.meta['offset'] < js['total-count']:
                nextPage = self.url_api.format(response.meta['category'], str(response.meta['offset']))
                yield Request(url=nextPage, callback=self.parse_essay, meta=response.meta)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = soup.select_one('.element-wrapper  p').text  # 无摘要，正文就是一大
        item['body'] = soup.select_one('.element-wrapper  p ').text
        item['images'] = []
        item['category2'] = response.meta['category2']
        item['pub_time'] = response.meta['pub_time']
        # self.logger.info('item item item item item item item item item item item item')
        return item



