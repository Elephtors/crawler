# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime

def devhoomimedia_time_switch1(time_string):
    # 返回时间戳
    # 2020-12-15T09:39:51+05:30
    return Util.format_time3(str(datetime.strptime(time_string.rsplit("+", 1)[0], "%Y-%m-%dT%H:%M:%S")))

def devhoomimedia_time_switch2(time_string):
    # 返回%Y-%m-%d %H:%M:%S
    # 2020-11-27T15:28:35+05:30
    time_string = time_string.rsplit("+", 1)[0]
    return datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")

# 将爬虫类名和name字段改成对应的网站名
class DevbhoomimediaSpider(scrapy.Spider):
    name = 'devbhoomimedia'
    website_id = 935  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.devbhoomimedia.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(DevbhoomimediaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = int(time) if time is not None else time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category1_url = []
        menu = soup.select(".tdc-header-wrap #td-header-menu #menu-main-menu-1 li a")
        for a in menu:
            url = a.get("href")
            if re.findall(r'https://www.devbhoomimedia.com/category/+\S+/\S', url):
                pass
            elif re.findall(r'https://www.devbhoomimedia.com/category/+\S+/', url) and url != "#":
                category1_url.append(url)
        for c1 in category1_url:
            yield scrapy.Request(c1, callback=self.parse_category1)

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        news_content = soup.select(
            "#td-outer-wrap .td-container .td-pb-span8.td-main-content .td-ss-main-content .td-block-row h3 a")
        for a in news_content:
            yield scrapy.Request(a.get("href"), callback=self.parse_detail)
        next_page = soup.select_one("#td-outer-wrap .td-container .td-pb-span8.td-main-content .td-ss-main-content "
                                    ".page-nav.td-pb-padding-side .page").get("href") if soup.select_one(
            "#td-outer-wrap .td-container .td-pb-span8.td-main-content .td-ss-main-content "
            ".page-nav.td-pb-padding-side .page") else None
        LastTimeStamp = devhoomimedia_time_switch1(soup.select("#td-outer-wrap .td-container "
        ".td-pb-span8.td-main-content .td-ss-main-content .td-block-row .td-block-span6")[-1].find("span",
                                                                class_="td-post-date").find("time").get("datetime"))
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
        category = soup.select(".td-crumb-container div span a")
        item['category1'] = category[1].text.strip()
        item['category2'] = category[2].text.strip() if len(category)>2 else None
        item['title'] = soup.select_one(".td-post-header header h1").text.strip()
        images = []
        image = soup.select(".td-post-featured-image a img") if soup.select(".td-post-featured-image a img") else None
        if image:
            for img in image:
                images.append(img.get("src"))
        item['images'] = images
        item['pub_time'] = devhoomimedia_time_switch2(soup.select_one(".td-post-header .td-post-date time").get("datetime"))
        abstract_list = soup.select(".td-post-content.tagdiv-type h3 span") if soup.select(".td-post-content.tagdiv-type h3 span") else None
        abstract = ""
        if abstract_list is not None:
            for a in abstract_list:
                abstract += a.text.strip() + "\n"
        item['abstract'] = abstract
        body_list = soup.select(".td-post-content.tagdiv-type h5 span")
        body = ""
        for b in body_list:
            body += b.text.strip() + "\n"
        item['body'] = body
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        yield item
