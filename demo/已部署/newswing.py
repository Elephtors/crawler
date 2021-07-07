import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests
import socket

class NwinSpider(scrapy.Spider):
    name = 'newswing'
    allowed_domains = ['newswing.com']
   # start_urls = ['http://newswing.com/']
    website_id = 1047  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(NwinSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(requests.get('https://newswing.com/').text, 'html.parser')
        for i in soup.select('#menu-main-navigation >li a'):
            meta = {'category1':i.text, 'category2':''}
            if re.match(r'^https://newswing.com/category/',i.get('href')):   # 过滤无效目录
                yield Request(url=i.get('href'), meta=meta)

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.post-details'):  # 每页的文章及其摘要
            strtt = i.find(class_='date meta-item tie-icon').text  # strtt 形如 '05/01/2021'
            pub_time = strtt.split('/')[2] + '-' + strtt.split('/')[1] + '-' + strtt.split('/')[0] + ' 00:00:00'
            if self.time is None or Util.format_time3(pub_time) >= int(self.time):
                response.meta['pub_time'] = pub_time
                yield Request(url=i.select_one('.post-title a').get('href'), meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            try:
                nextPage = soup.select_one('div.pages-nav a').get('href') if soup.select_one('div.pages-nav a').get('href') else None
                if nextPage:  # 有下一页就翻页
                    yield Request(url=nextPage, meta=response.meta)
            except:
                self.logger.info('Next page no more')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = soup.select_one('div.entry-header>h1').text
        # strtt = soup.select_one('#single-post-meta > span:nth-of-type(2)').text  # strtt 形如 '05/01/2021'
        item['pub_time'] = response.meta['pub_time']# strtt.split('/')[2]+'-'+strtt.split('/')[1]+'-'+strtt.split('/')[0]+' 00:00:00'
        item['images'] = [i.get('src') for i in soup.select('figure.single-featured-image img')]
        ss = ''
        for p in soup.select('div.featured-area ~ div')[0].select('p'):
            ss += p.text
            ss += '\n'
        item['body'] = ss
        item['abstract'] =soup.select('div.featured-area ~ div')[0].select('p')[0].text
        return item