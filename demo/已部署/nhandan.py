# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime

def nhandan_time_switch1(time_string):
    # 2020年12月25日 星期五
    # 返回时间戳
    time_string = time_string.rsplit(" ", 1)[0]
    return Util.format_time3(str(datetime.strptime(time_string, "%Y年%m月%d日")))

def nhandan_time_switch2(time_string):
    # 2020年12月25日 星期五, 18:39:11
    # 返回datetime格式时间
    time_string = re.split(", | ", time_string)[0] + re.split(", | ", time_string)[2] # 2020年12月25日18:39:11
    return datetime.strptime(time_string, "%Y年%m月%d日%H:%M:%S")


# 将爬虫类名和name字段改成对应的网站名
class NhandanSpider(scrapy.Spider):
    name = 'nhandan'
    website_id = 1249     # 网站的id(必填)
    language_id = 1813  # 所用语言的id
    start_urls = ['https://cn.nhandan.com.vn/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(NhandanSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = int(time) if time is not None else time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        for a in soup.select(".nd_header_menu #topnav .nav.navbar-nav li a"):
            url = 'https://cn.nhandan.com.vn' + a.get("href") if a.get("href") != "#" else None
            if url is not None:
                yield scrapy.Request(url, callback=self.parse_category1)

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        for a in soup.select(".row .col-sm-8.col-xs-12 div.media h4 .pull-left") + soup.select(".row .col-sm-12.col-xs-12 .col-sm-12.col-xs-12 .media-body h3 a"):
            news_url = 'https://cn.nhandan.com.vn' + a.get("href")
            yield scrapy.Request(news_url, callback=self.parse_detail)
        next_page = 'https://cn.nhandan.com.vn' + soup.select_one("ul.pager li.next a").get("href")
        LastTimeStamp = nhandan_time_switch1(soup.select(".row .col-sm-12.col-xs-12 .col-sm-12.col-xs-12 h5 .text-muted")[-1].text.strip())
        if self.time is None or LastTimeStamp >= self.time:
            if next_page:
                yield scrapy.Request(next_page, callback=self.parse_category1)
            else:
                self.logger.info("该目录已经到底")
        else:
            self.logger.info("时间截止")

    def parse_detail(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        item = DemoItem()
        item['title'] = soup.select_one(".row .media .fontM.ndtitle h3").text.strip()
        item['abstract'] = soup.select_one(".row .media .ndcontent").text.strip()
        item['pub_time'] = nhandan_time_switch2(soup.select_one(".icon_date_top .pull-left").text.strip())
        body = ""
        for b in soup.select(".row .media .ndcontent"):
            body += b.text.strip()+"\n"
        item['body'] = body
        item['category1'] = soup.select(".row ul.breadcrumb li")[-1].text.strip()
        item['category2'] = None
        images = []
        for img in soup.select(".media .nd_img"):
            images.append("https://cn.nhandan.com.vn/" + img.get("src"))
        item['images'] = images
        yield item
