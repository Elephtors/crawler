import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import json

class piagov(scrapy.Spider):# cyl
    name = 'piagov'
    # allowed_domains = ['https://pia.gov.ph/']
    start_urls = ['https://pia.gov.ph/']
    website_id = 1231  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(piagov, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['category1'] = ''
        meta['request_url'] = ''
        meta['page_number'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        menu_url = html.select("div#navbar li.nav-item>a")
        yield scrapy.Request(menu_url[2]['href'], meta=response.meta, callback=self.parse_category2)

    def parse_category2(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        cat1s = html.select("ul.list-unstyled>li>a")
        cat_list = []
        for i in range(4, 7):
            cat_list.append(cat1s[i])
        for c in cat_list:
            cat1 = c.text
            response.meta['category1'] = cat1
            cat1_url = c['href']
            yield scrapy.Request(cat1_url, meta=response.meta, callback=self.parse_category3, dont_filter=True)

    def parse_category3(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        cat2s = html.select("div.listing-container li.category.grouping a")
        for c in cat2s:
            response.meta['category2'] = c.text
            cat2_url = c['href']
            response.meta['request_url'] = cat2_url
            page_number = 1
            response.meta['page_number'] = page_number
            yield scrapy.Request(cat2_url, meta=response.meta, callback=self.parse_category4, dont_filter=True)

    def parse_category4(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        page_number = response.meta['page_number']
        request_url1 = response.meta['request_url']
        request_url = request_url1 + ".json?p=" + str(page_number)
        data = {
            'page': str(page_number)
        }
        response.meta['page_number'] = response.meta['page_number'] + 1
        yield scrapy.FormRequest.from_response(response, url=request_url, formdata=data, method='POST', meta=response.meta,
                                               callback=self.parse_category5)

    def parse_category5(self, response):
        page_number = response.meta['page_number']
        ex = 'https://pia.gov.ph/(.*?)/.*?/.*?'
        request_url1 = response.meta['request_url']
        cat = re.findall(ex, request_url1)[0]
        request_url = request_url1 + ".json?p=" + str(page_number)
        data = {
            'page': str(page_number)
        }
        if 'articles' in json.loads(response.body).keys():
            article = json.loads(response.body)['articles']
            if len(article) == 1:
                pass
            else:
                for a in article:
                    detail_url = a['url']
                    yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_detail)

                if 'iso' in article[-1]['headlineDate']['timeStamp'].keys():
                    ddl = article[-1]['headlineDate']['timeStamp']['iso']
                    ex = '(\d{4}).*?'
                    year = re.findall(ex, ddl)[0]
                    if year == '0000':
                        ex = '\d{4}(-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
                        no_year = re.findall(ex, ddl)[0]
                        ddl = '2020' + no_year
                    ddl = Util.format_time3(ddl)
                else:
                    ddl = None
                if (self.time == None or ddl >= int(self.time)):
                    response.meta["page_number"] = response.meta['page_number'] + 1
                    yield scrapy.FormRequest(url=request_url, formdata=data, method='POST',
                                             meta=response.meta, callback=self.parse_category5)
                else:
                    self.logger.info('时间截止')
                    pass

    def parse_detail(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text, 'html.parser')
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one("div.container h1") is not None:
            item['title'] = html.select_one("div.container h1").text
        item['body'] = ''
        if html.select("div.col-24 p"):
            bodies = html.select("div.col-24 p")
            b_list = [b.text for b in bodies]
            item['body'] = '\n'.join(b_list)
            item['abstract'] = bodies[0].text
        item['images'] = []
        if html.select("div.col-24 figure img"):
            images = html.select("div.col-24 figure img")
            for i in images:
                item['images'].append(i['src'])
        if html.select_one("p.byline span.date") is not None:
            ex = 'Published on (.*)'
            pub_time = html.select_one("p.byline span.date").text
            pub_time = re.findall(ex, pub_time)
            if pub_time:
                pub_time = pub_time[0]
                pub_time = Util.format_time2(pub_time)
                item['pub_time'] = pub_time
            else:
                item['pub_time'] = Util.format_time()
        else:
            item['pub_time'] = Util.format_time()
        yield item