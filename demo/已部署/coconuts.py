import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class coconuts(scrapy.Spider):# cyl
    name = 'coconuts'
    start_urls = ['https://coconuts.co/']
    website_id = 1247  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(coconuts, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['page_number'] = ''
        meta['request_url'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cat1s = html.select("ul.main-menu.list-float li a")
        for c in cat1s:
            cat1 = c.text.strip()
            if cat1 in ['Join COCO+', 'Newsletters', 'SHOP']:
                continue
            meta['category1'] = cat1
            cat1_url = c['href']
            yield scrapy.Request(cat1_url, meta=meta, callback=self.parse_category2)

    def parse_category2(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        cat2s = html.select("ul.global-navbar__links-main.global-navbar__links li a")
        for c in cat2s:
            cat2 = c.text.strip()
            if cat2 in ['Join COCO+', 'Newsletters', 'SHOP']:
                continue
            response.meta['category2'] = cat2
            cat2_url = c['href']
            # self.logger.info('第二个'+cat2_url)
            yield scrapy.Request(cat2_url, meta=response.meta, callback=self.parse_category3)

    def parse_category3(self, response):
        request_url1 = response.url
        response.meta['request_url'] = request_url1
        page_number = 1
        response.meta['page_number'] = page_number
        request_url = request_url1 + 'page/' + str(page_number) + '/'
        # self.logger.info('第三个'+request_url)
        yield scrapy.Request(request_url, meta=response.meta, callback=self.parse_category4, dont_filter=True)


    def parse_category4(self, response):
        if response.status == int(200):
            page_number = response.meta['page_number']
            html = BeautifulSoup(response.text, "html.parser")
            details = html.select("div.co-river__entry")
            for d in details:
                detail_url = d.select_one("a.today-news-link")['href']
                yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_category5)
            if details:
                ddl = details[-1].select_one("time").text
                ddl = Util.format_time2(ddl)
                ddl = Util.format_time3(ddl)
            else:
                ddl = None
            if (self.time == None or (ddl != None and ddl >= int(self.time))):
                response.meta['page_number'] = response.meta['page_number'] + 1
                request_url1 = response.meta['request_url']
                request_url = request_url1 + 'page/' + str(response.meta['page_number']) + '/'
                # self.logger.info('第四个'+request_url)
                yield scrapy.Request(request_url, meta=response.meta, callback=self.parse_category4)
            else:
                self.logger.info('时间截止')
        else:
            pass

    def parse_category5(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one("h1.post-title") is not None:
            item['title'] = html.select_one("h1.post-title").text
        item['body'] = ''
        item['images'] = []
        if html.select('div.post-body p'):
            bodies = html.select('div.post-body p')
            b_list = [b.text for b in bodies]
            item['body'] = '\n'.join(b_list)
            item['abstract'] = bodies[0].text
            for b in bodies:
                if b.select_one("iframe") is not None:
                    item['images'].append(b.select_one("iframe")['src'])
        if html.select_one("figure img") is not None:
            item['images'].append(html.select_one("figure img")['src'])
        if html.select_one("time.post-timeago ") is not None:
            pub_time = html.select_one("time.post-timeago ")['datetime']
            pub_time = Util.format_time2(pub_time)
            item['pub_time'] = pub_time
        yield item
