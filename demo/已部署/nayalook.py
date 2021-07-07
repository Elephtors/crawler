# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime


def nayalook_time_switch1(time_string):
    # 30/11/2020
    # 返回时间戳
    return Util.format_time3(str(datetime.strptime(time_string, "%d/%m/%Y")))


def nayalook_time_switch1_2(time_string):
    # 3 days ago
    # 返回时间戳
    return Util.format_time3(str(Util.format_time2(time_string)))


def nayalook_time_switch2(time_string):
    # 返回%Y-%m-%d %H:%M:%S
    # 3 days ago
    return Util.format_time2(time_string)

def nayalook_time_switch2_2(time_string):
    # 返回%Y-%m-%d %H:%M:%S
    # 30/11/2020
    return datetime.strptime(time_string, "%d/%m/%Y")


# 将爬虫类名和name字段改成对应的网站名
class NayalookSpider(scrapy.Spider):
    name = 'nayalook'
    website_id = 934  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.nayalook.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(NayalookSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = int(time) if time is not None else time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        menu = soup.select(".container #main-nav-menu ul li a")
        category1_url = []
        for m in menu:
            url = m.get("href")
            if re.match("https://www.nayalook.com/category/+\S+/+\S+/", url):
                pass
            else:
                if url != "#" and url.rsplit("/", 2)[-2] not in ["e-paper", "studio"]:
                    category1_url.append(url)
        for c1 in category1_url:
            yield scrapy.Request(c1, callback=self.parse_category1)

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        news_content = soup.select(".container-wrapper ul#posts-container li")
        for n in news_content:
            news_url.append(n.find("a").get("href"))
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_detail)
        next_page = soup.select_one(".pages-nav div span a").get("href") if soup.select_one(
            ".pages-nav div span a") else None
        try:
            LastTimeStamp = nayalook_time_switch1(
                soup.select(".post-details .post-meta.clearfix .date.meta-item.tie-icon")[-1].text.strip())
        except:
            LastTimeStamp = nayalook_time_switch1_2(soup.select(".post-details .post-meta.clearfix "
                                                                ".date.meta-item.tie-icon")[-1].text.strip())
        if self.time is None or LastTimeStamp >= self.time:
            if next_page:
                yield scrapy.Request(next_page, callback=self.parse_category1)
            else:
                self.logger.info("该目录已经到底")
        else:
            self.logger.info("时间截止")

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features="lxml")
        item['category1'] = soup.select("nav#breadcrumb a")[1].text.strip()
        item['category2'] = soup.select("nav#breadcrumb a")[2].text.strip() if len(soup.select("nav#breadcrumb a"))==3 else None
        item['title'] = soup.select_one(".entry-header h1").text.strip()
        try:
            item['pub_time'] = nayalook_time_switch2(
                soup.select_one(".entry-header #single-post-meta .date.meta-item.tie-icon").text.strip())
        except:
            item['pub_time'] = nayalook_time_switch2_2(
                soup.select_one(".entry-header #single-post-meta .date.meta-item.tie-icon").text.strip())
        images = []
        image = soup.select(".featured-area figure img")
        for img in image:
            images.append(img.get("src"))
        item['images'] = images
        body_content = soup.select(".entry-content.entry.clearfix p")
        body = ""
        for b in body_content:
            body += b.text.strip() + "\n"
        item['body'] = body
        item['abstract'] = body_content[0].text.strip()
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        yield item
