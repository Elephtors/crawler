import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import json
import requests
import socket

class topgearSpider(scrapy.Spider):
    name = 'topgear'
    website_id = 487 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    categorys = [
        'car-reviews',
        'big-test',
        'car-news',
        'industry-news',
        'motoring-news',
        'racing-news',
        'technology-news',
        'feature-articles',
        'lifestyle',
        'tip-sheet',
        'head-over-wheels',
        'rust-n-pieces',
        'the-decision',
        'motor-mouth-online',
        'wheels-of-justice',
        'launch-pad',
        'motorcycle-news',
        'motorcycle-feature',
        'motorcycle-review',
    ]

    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(topgearSpider, self).__init__(*args, **kwargs)
        self.time = time

    def start_requests(self):
        socket.setdefaulttimeout(30)
        category1 = 'launch-pad'
        for category in self.categorys:

            if category=='car-reviews' or category=='big-test':
                category1 = 'drives'
            elif category=='car-news' or category=='industry-news' or category=='motoring-news' or category=='racing-news' or category=='technology-news':
                category1 = 'news'
            elif category=='feature-articles' or category=='lifestyle' or category=='tip-sheet':
                category1 = 'features'
            elif category=='head-over-wheels' or category=='rust-n-pieces' or category=='the-decision' or category=='motor-mouth-online' or category=='wheels-of-justice':
                category1 = 'columns'
            elif category=='motorcycle-news' or category=='motorcycle-feature' or category=='motorcycle-review':
                category1 = 'moto-sapiens'

            for i in range(0,100000):
                js = json.loads(requests.get('https://api.summitmedia-digital.com/topgear/v1/channel/get/{}/{}/{}'.format(category,i,10),headers=self.header).text)
                if len(js)==0 or (self.time != None and js[0]['date_published'] < int(self.time)):
                    self.logger.info('截止')
                    break
                else:
                    for j in js:
                        yield Request('https://www.topgear.com.ph/'+j['url'],meta={'category1':category1,'category2':category})

    def parse(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['title'] = html.select('.ch ~ div > h1')[0].text
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['body'] = ''
        flag = False
        for i in html.select('p'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('.card__body')[0].text)
        item['images']=[]
        for i in html.select('p img'):
            item['images'].append(i.attrs['src'])
        yield item
