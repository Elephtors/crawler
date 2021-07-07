# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime
import requests
import socket

def khulasaa_time_switch(time_String):
    # November 8, 2020, 7:26 pm
    # 返回 %Y-%m-%d %H:%M:%S
    return datetime.strptime(time_String, "%B %d, %Y, %I:%M %p")


# 将爬虫类名和name字段改成对应的网站名
class KhulasaaSpider(scrapy.Spider):
    name = 'khulasaa'
    website_id = 926  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.khulasaa.in/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(KhulasaaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = int(time) if time is not None else time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category1_url = []
        menu = soup.select("#fixedMenu .g-header__inner #navbar li")[1:]
        for m in menu:
            category1_url.append(m.find("a").get("href"))
        for c1 in category1_url:
            yield scrapy.Request(c1, callback=self.parse_category1)

    def parse_category1(self, response):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        news_content = soup.select(".o-article .k-list-sec .allBox ul li")
        for n in news_content:
            news_url.append(n.find("a").get("href"))
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_detail)
        next_page = soup.select_one(".o-listing .pagination a").get("href") if soup.select_one(".o-listing .pagination a") else None
        LastTimeStamp = Util.format_time3(str(khulasaa_time_switch(BeautifulSoup(requests.get(news_url[-1]).text, features="lxml").select_one(".author-disc .date .author span").text)))
        if next_page:
            if self.time is None or LastTimeStamp >= self.time:
                yield scrapy.Request(next_page, callback=self.parse_category1)
            elif LastTimeStamp < self.time:
                self.logger.info("$$$时间截止$$$")
        else:
            self.logger.info("$$$该页已经到底$$$")

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features="lxml")
        item['title'] = soup.select_one(".o-article .entry-content h1").text.strip()
        item['pub_time'] = khulasaa_time_switch(soup.select_one(".author-disc .date .author span").text)
        images = []
        for img in soup.select(".content-section .featured-box img"):
            images.append(img.get("src"))
        item['images'] = images
        abstract = ""
        for a in soup.select(".post-content ul li h3"):
            abstract += a.text.strip()
            abstract += "\n"
        item['abstract'] = abstract
        body = ""
        for b in soup.select(".post-content p"):
            body += b.text.strip()
        item['body'] = body
        item['category1'] = soup.select_one(".breadcrumb span span span a").text.strip()
        item['category2'] = None
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        yield item
