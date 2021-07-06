# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
from datetime import datetime
import time


def therocket_time_switch(time_string):
    # June 27, 2021
    # 返回时间戳
    return datetime.strptime(time_string, "%B %d, %Y")


class TherocketSpider(scrapy.Spider):
    name = 'therocket_spider'
    website_id = 140  # 网站的id(必填)
    language_id = 1814  # 所用语言的id
    start_urls = ['https://therocket.com.my/cn/']
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cbs',
        'password': 'dg_cbs',
        'db': 'dg_test_source'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(TherocketSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_list = [a.get("href") for a in soup.select_one("#td-header-menu").select("div #menu-td-demo-footer"
                                                                                          "-menu-1 li a")]
        for url in category_list:
            if re.match("https://therocket.com.my/cn/category/", url):
                yield scrapy.Request(url, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        for news_url in [h3.get("href") for h3 in soup.select(".td-ss-main-content h3.entry-title.td-module-title a")]:
            yield scrapy.Request(news_url, callback=self.parse_detail)
        next_num = int(soup.select_one(".page-nav.td-pb-padding-side .current").text) + 1
        last_num = int(soup.select_one(".page-nav.td-pb-padding-side .last").text)
        LastTimeStamp = therocket_time_switch(
            soup.select(".td-ss-main-content .td-module-meta-info .td-post-date")[-1].text)
        if self.time is None or LastTimeStamp >= self.time:
            if next_num <= last_num:
                yield scrapy.Request(response.url + 'page/' + str(next_num), callback=self.parse_detail)
            else:
                self.logger.info("目录已经到底")
        else:
            self.logger.info("时间截止")

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features="lxml")
        item['title'] = soup.select_one("header.td-post-title h1").text
        item['images'] = [a.get("href") for a in soup.select(".td-post-featured-image a")] if soup.select(".td-post-featured-image a") else []
        body_list = [b.text for b in soup.find_all("div", dir="auto")]
        item['body'] = "\n".join(body_list)
        item['abstract'] = body_list[0]
        item['pub_time'] = therocket_time_switch(soup.select_one(".td-post-date").text)
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        item['category1'] = soup.select_one(".entry-category").text
        item['category2'] = None
        yield item