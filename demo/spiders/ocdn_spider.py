# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
from datetime import datetime
import time
import re

def ocdn_time_switch1(time_string):
    # July 06, 2021
    # 返回时间戳
    return Util.format_time3(str(datetime.strptime(time_string, "%B %d, %Y")))

def ocdn_time_switch2(time_string):
    #  Wednesday, July 07, 2021
    # 返回时间
    return datetime.strptime(time_string, " %A, %B %d, %Y")

# 将爬虫类名和name字段改成对应的网站名
class OcdnSpider(scrapy.Spider):
    name = 'ocdn_spider'
    website_id = 145  # 网站的id(必填)
    language_id = 2266  # 所用语言的id
    start_urls = ['http://www.ocdn.com.my/']
    sql = {  # sql配置
        'host': '121.36.242.178',
        'user': 'dg_cbs',
        'password': 'dg_cbs',
        'db': 'dg_test_source'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(OcdnSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        for category_url in [response.url + a.get("href") + "?pageNo=1" for a in soup.select(".mobile-bg .nav.navbar-nav.nav-cust li a")[1:9]]:
            yield scrapy.Request(category_url, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        if soup.select_one(".headlines") is None:
            self.logger.info("该目录已经到底")
            return
        else:
            for news_url in ["http://www.ocdn.com.my/"+a.get("href") for a in soup.select(".row div.headlines .title a")]:
                yield scrapy.Request(news_url, callback=self.parse_detail)
            LastTimeStamp = ocdn_time_switch1(soup.select(".row div.headlines .content div")[-1].text)
            next_page = response.url.split("=")[0]+"="+str(int(response.url.split("=")[1])+1)
            if self.time is None or LastTimeStamp >= int(self.time):
                # self.logger.info(next_page+"下一页就是这个")
                yield scrapy.Request(next_page, callback=self.parse_category)
            else:
                self.logger.info("时间截止")

    def parse_detail(self, response):
        soup = BeautifulSoup(response.text, features='lxml')
        item = DemoItem()
        item['title'] = soup.select_one(".headlines .title.titlemobile").text
        item['pub_time'] = ocdn_time_switch2(soup.select(".headlines div")[1].text.split(":")[1])
        item['images'] = ["http://www.ocdn.com.my/"+img.get("src") for img in soup.select(".imgcaptiondiv img")] if soup.select(".imgcaptiondiv img") else []
        body_text = soup.select_one(".row .headlines").text.strip()
        if re.match("\t\r\n\t\t\t", body_text) and re.match("\r\n\r\n\nADVERTISEMENT\n", body_text):
            item['body'] = body_text.split("\t\r\n\t\t\t")[1].replace("\r\n\r\n\nADVERTISEMENT\n", "")
        else:
            item['body'] = body_text
        item['abstract'] = item['body'].split("\r\n")[0] if item['body'].split("\r\n")[0] else None
        item['category1'] = soup.select_one(".row .crumb").text.strip().split("/ ")[1] if soup.select_one(".row .crumb") else None
        item['category2'] = None
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        yield item
