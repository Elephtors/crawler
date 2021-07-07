import json
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class BhopalsamacharSpider(scrapy.Spider):
    name = 'bhopalsamachar'
    allowed_domains = ['bhopalsamachar.com']
    start_urls = ['https://www.bhopalsamachar.com/']
    website_id = 1054  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    api_url = 'https://www.bhopalsamachar.com/search/label/{}?updated-max={}'

    def __init__(self, time=None, *args, **kwargs):
        super(BhopalsamacharSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#main-menu-nav a'):
            if re.findall('label', i.get('href')):
                meta = {'category1': i.text, 'category2': None, 'category':i.get('href').split('/')[-1]}
                yield Request(url=i.get('href'), meta=meta, callback=self.parse_essay)
            else:
                self.logger.info('Wrong URL: '+ i.get('href'))
                continue

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True  # 判定时间是否截止
        nextPage = True  # 判定 是否到了最后一页
        try:
            tt = soup.select('.post-author ~ span')[-1].get('datetime').split('T')
            last_pub_time = tt[0]+' '+tt[1].split('+')[0]
        except:
            nextPage = False
            self.logger.info('Next Page No More')
        if self.time is None or (Util.format_time3(last_pub_time)) >= int(self.time):
            for i in soup.find_all(class_='blog-post hentry index-post'):
                response.meta['title'] = i.select_one('.post-title').text
                tt = soup.select_one('.post-author ~ span').get('datetime').split('T')
                response.meta['pub_time'] = tt[0]+' '+tt[1].split('+')[0]
                response.meta['images'] = [i.select_one('img').get('src')]
                response.meta['abstract'] = soup.select_one('.post-snippet').text
                yield Request(url=i.select_one('.post-title>a').get('href'), callback=self.parse_item, meta=response.meta)
        else:
            flag = False
            self.logger.info('时间截止')
        if flag and nextPage:
            last = soup.select('.post-author ~ span')[-1].get('datetime').replace(':', '%3A').replace('+', '%2B')
            url = self.api_url.format(response.meta['category'], last)
            print(url)
            yield Request(url=url, callback=self.parse_essay, meta=response.meta)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = response.meta['abstract']
        ss = ''
        for i in soup.find_all(attrs={'style':'text-align: justify;'}):
            ss += i.text + '\n'
        item['body'] = ss
        item['images'] = response.meta['images']
        item['category2'] = response.meta['category2']
        item['pub_time'] = response.meta['pub_time']
        return item