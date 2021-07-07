
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
from datetime import datetime
import time

def centralindia_time_switch1(time_string):
    # March 14, 2021
    # 返回时间戳
    return time.mktime(time.strptime(time_string, "%B %d, %Y"))

def centralindia_time_switch2(time_string):
    # 2021-03-22T15:34:27+00:00
    return time_string.split("+")[0].replace('T',' ')

#将爬虫类名和name字段改成对应的网站名
class CentralindiaSpider(scrapy.Spider):
    name = 'centralindia'
    website_id = 952 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['https://www.centralindia.news/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(CentralindiaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], headers=self.headers, callback=self.parse)

    def parse(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        category1_url = []
        menu = soup.select(".menu-main-menu-container ul#menu-main-menu-1 li a")
        for a in menu:
            url = a.get("href")
            if re.match("https://www.centralindia.news/category/", url) and url not in category1_url:
                category1_url.append(url)
        for url in category1_url:
            yield scrapy.Request(url, callback=self.parse_category1)

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        if soup.select_one(".td-ss-main-content div") is None or soup.select_one(".td-404-title"):
            return
        news = soup.select(".td-ss-main-content .td-module-thumb a")
        for a in news:
            yield scrapy.Request(a.get("href"), callback=self.parse_detail)
        next_page = soup.select(".page-nav.td-pb-padding-side a")[-1].get("href") if soup.select(".page-nav.td-pb-padding-side a i.td-icon-menu-right") else None
        LastTimeStamp = centralindia_time_switch1(soup.select(".td-ss-main-content div span.td-post-date")[-1].text.strip())
        if self.time is None or LastTimeStamp >= int(self.time):
            if next_page is not None:
                yield scrapy.Request(next_page, callback=self.parse_category1)
            else:
                self.logger.info("该目录到底")
        else:
            self.logger.info("时间截止")

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['title'] = soup.select_one("div.td-ss-main-content .td-post-header header h1").text.strip()
        item['pub_time'] = centralindia_time_switch2(soup.select_one(".td-module-meta-info time").get("datetime"))
        images = soup.select(".td-post-content .td-post-featured-image a img")
        item['images'] = [img.get("src") for img in images]
        item['abstract'] = soup.select(".td-post-content p")[0].text.strip()
        item['body'] = ""
        for p in soup.select(".td-post-content p"):
            item['body'] += p.text.strip() + '\n'
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        item['category1'] = soup.select(".entry-crumbs span")[-2].text.strip()
        item['category2'] = None
        yield item



