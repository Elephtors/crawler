import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}

class clickthecity(scrapy.Spider):# cyl
    name = 'clickthecity'
    # allowed_domains = ['https://www.clickthecity.com/']
    start_urls = ['https://www.clickthecity.com/']
    website_id = 1248  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(clickthecity, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['abstract'] = ''
        meta['page_number'] = ''
        meta['request_url'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        long_list = html.select("div.elementor-row>div")
        long_list1 = long_list[7].select("div>div>div")
        long_list2 = long_list1[1].select("ul li>a")
        for i in long_list2:
            if i.select_one("span").text in ['Privileges']:
                continue
            elif i.select_one("span").text in ['Events', 'Campus']:
                category1 = i.select_one("span").text
                meta['category1'] = category1  # 获取标题
                detial_list_url = "https://www.clickthecity.com" + i['href']
                yield scrapy.Request(detial_list_url, meta=meta, callback=self.parse_special_1)
            else:
                category1 = i.select_one("span").text
                meta['category1'] = category1  # 获取标题
                detial_list_url = "https://www.clickthecity.com" + i['href']
                yield scrapy.Request(detial_list_url, meta=meta, callback=self.parse_category2)

    def parse_special_1(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        page_number = 1
        response.meta['page_number'] = page_number
        response.meta['request_url'] = response.url
        special_url = response.url + 'page/' + str(page_number) + '/'
        response.meta['page_number'] = response.meta['page_number'] + 1
        yield scrapy.Request(special_url, meta=response.meta, callback=self.parse_special_2, dont_filter=True)

    def parse_special_2(self, response):
        if response.status == int(200):
            page_number = response.meta['page_number']
            request_url1 = response.meta['request_url']
            html = BeautifulSoup(response.text, "html.parser")
            details = html.select("div#blog-entries article")
            if details:
                for d in details:
                    if d.select_one("div.blog-entry-summary.clr p") is not None:
                        response.meta['abstract'] = d.select_one("div.blog-entry-summary.clr p").text.strip()
                    new_detail_url = d.select_one("h2.blog-entry-title.entry-title a")['href']
                    yield scrapy.Request(new_detail_url, meta=response.meta, callback=self.parse_category3)

            if html.select("div#blog-entries article")[-1].select_one("div.blog-entry-date.clr") is not None:
                ddl = html.select("div#blog-entries article")[-1].select_one("div.blog-entry-date.clr").text.strip()
                ddl = Util.format_time2(ddl)
                ddl = Util.format_time3(ddl)
            else:
                ddl = None

            if (self.time == None or ddl >= int(self.time)):
                request_url = request_url1 + 'page/' + str(page_number) + '/'
                response.meta['page_number'] = response.meta['page_number'] + 1
                yield scrapy.Request(request_url, meta=response.meta, callback=self.parse_special_2)
            else:
                self.logger.info('时间截止')
                pass
        else:
            pass

    def parse_category2(self, response):
        html = BeautifulSoup(response.text)
        details = html.select("div.elementor-widget-container article")
        if details:
            for d in details:
                if d.select_one("div.elementor-post__excerpt p") is not None:
                    response.meta['abstract'] = d.select_one("div.elementor-post__excerpt p").text.strip()  # 获取摘要
                if d.select_one("h3.elementor-post__title a") is not None:
                    detail_url = d.select_one("h3.elementor-post__title a")['href']
                    yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_category3)
        # 翻页
        if html.select("span.elementor-post-date"):
            ddl = html.select("span.elementor-post-date")[-1].text.strip()
            ddl = Util.format_time2(ddl)
            ddl = Util.format_time3(ddl)
        else:
            ddl = None

        if html.select_one("a.page-numbers.next") is not None:
            next_page = html.select_one("a.page-numbers.next")
            next_page_url = next_page['href']
            if (self.time == None or ddl >= int(self.time)):
                yield scrapy.Request(next_page_url, meta=response.meta, callback=self.parse_category2)
            else:
                self.logger.info('时间截止')


    def parse_category3(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select_one("div.elementor-widget-container h1") is not None:
            item['title'] = html.select_one("div.elementor-widget-container h1").text
        item['body'] = ''
        if html.select("div.elementor-widget-container p"):
            bodies = html.select("div.elementor-widget-container p")
            for b in bodies:
                item['body'] += b.text
                item['body'] += '\n '
        item['abstract'] = response.meta['abstract']
        item['images'] = []
        if html.select_one("div.elementor-image img") is not None:
            item['images'].append(html.select_one("div.elementor-image img")['src'])
        if html.select("div.elementor-widget-container figure img"):
            images = html.select("div.elementor-widget-container figure img")
            for i in images:
                item['images'].append(i['src'])
        if html.select_one(
                "span.elementor-icon-list-text.elementor-post-info__item.elementor-post-info__item--type-date") is not None:
            pub1 = html.select_one(
                "span.elementor-icon-list-text.elementor-post-info__item.elementor-post-info__item--type-date").text.strip()
            if html.select_one(
                    "span.elementor-icon-list-text.elementor-post-info__item.elementor-post-info__item--type-time") is not None:
                pub2 = html.select_one(
                    "span.elementor-icon-list-text.elementor-post-info__item.elementor-post-info__item--type-time").text.strip()
                ex = '(.*?) .*?m.*?'
                pub2 = re.findall(ex, pub2)
                if pub2:
                    pub = pub1 + " " + pub2[0]
                    if pub is not None:
                        pub_time = Util.format_time2(pub)
                        item['pub_time'] = pub_time
                else:
                    pub = pub1
                    pub_time = Util.format_time2(pub)
                    item['pub_time'] = pub_time
        yield item
