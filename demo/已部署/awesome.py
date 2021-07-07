# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re


class awesome(scrapy.Spider):
    name = 'awesome'
    # allowed_domains = ['https://awesome.blog/']
    start_urls = ['https://awesome.blog/']
    website_id = 1243  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(awesome, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['abstract'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        menu = html.select("ul.sub-menu li a")
        for i in menu:  # #Restaurants
            ex = '.(.*)?'
            f_cat = i.text
            cat = re.findall(ex, f_cat)[0]  # Restaurants
            meta['category1'] = cat  # 获取一级目录
            detail_list_url = i['href']  # 获取一级目录对应url
            yield scrapy.Request(detail_list_url, meta=meta, callback=self.parse_category2)

    def parse_category2(self, response):
        html = BeautifulSoup(response.text)
        details = html.select("main#main article")
        for d in details:
            detail_url = d.select_one("header.entry-header h2 a")['href']
            response.meta['abstract'] = d.select_one("div.entry-content p").text  # 获取摘要
            yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_category3)

        if html.select("time.entry-date.published"):
            ddl = html.select_one("time.entry-date.published")['datetime']  # datetime="2021-01-30T23:00:00+08:00"
            ddl = re.split('T|\+', ddl)  # ['2021-01-30', '23:00:00', '08:00']
            ddl = ddl[0] + ' ' + ddl[1]  # 2021-01-30 23:00:00
            ddl = Util.format_time3(ddl)  # 1612018800
        else:
            ddl = None
        # 翻页
        next_page = html.select("div.nav-links div.nav-previous")
        if next_page:
            next_page_url = next_page[0].select_one("a")['href']
            if (self.time == None or (ddl != None and ddl >= int(self.time))):
                yield scrapy.Request(next_page_url, meta=response.meta, callback=self.parse_category2)
            else:
                self.logger.info('时间截止')

    def parse_category3(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.select("h1.entry-title"):  # 获取标题
            item['title'] = html.select_one("h1.entry-title").text
        item['body'] = ''  # 获取正文内容
        body_list = html.select("div.entry-content p")
        if body_list:
            for b in body_list:
                item['body'] += b.text
                item['body'] += "\n"
        item['abstract'] = response.meta['abstract']
        item['images'] = []  # 获取图片链接
        images = html.select("div.entry-content figure.wp-block-image size-large")
        if images:
            for i in images:
                item['images'].append(i.select_one("img")['src'])
        pub1 = html.select("div.posted-on time")  # 获取发布时间
        if pub1:
            pub_time = html.select_one("div.posted-on time").text.strip()
            item['pub_time'] = Util.format_time2(pub_time)
        yield item
