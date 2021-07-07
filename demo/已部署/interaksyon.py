import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class interaksyonSpider(scrapy.Spider):
    name = 'interaksyon'
    website_id = 490 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://interaksyon.philstar.com/news/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(interaksyonSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('.td-ss-main-content .td-module-thumb > a'):
            yield Request(i.attrs['href'],callback=self.parse1)
        if self.time == None or Util.format_time3(Util.format_time2(html.select('.td-ss-main-content > div time')[-1].text)) >= int(self.time):
            yield Request(html.select('.page-nav.td-pb-padding-side > a')[-1].attrs['href'],callback=self.parse)
        
    def parse1(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text)
        list = response.url.split('/')
        item['title'] = html.select('.entry-title')[0].text
        item['category1'] = list[3]
        item['body'] = ''
        flag = False
        for i in html.select('.td-post-content.td-pb-padding-side p'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('header > .meta-info')[0].text)
        item['images'] = []
        for i in html.select('.td-post-featured-image img'):
            item['images'].append(i.attrs['src'])
        yield item
