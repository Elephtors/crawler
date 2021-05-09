<<<<<<< HEAD:demo/spiders/latestnews1_spider.py
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime

def lastestnews1_time_switch1(time_string):
    # 2020-12-23T17:50:27+05:30
    # 返回时间戳
    time_string = time_string.rsplit("+", 1)[0]
    return Util.format_time3(str(datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")))

def lastestnews1_time_switch2(time_string):
    # 2020-12-23T17:50:27+05:30
    # 返回%Y-%m-%d %H:%M:%S
    time_string = time_string.rsplit("+", 1)[0]
    return datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")

# 将爬虫类名和name字段改成对应的网站名
class Latestnews1Spider(scrapy.Spider):
    name = 'latestnews1_spider'
    website_id = 936  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.latestnews1.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cbs',
        'password': 'dg_cbs',
        'db': 'dg_test'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(Latestnews1Spider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = int(time) if time is not None else time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category1_url = []
        menu = soup.select("#header-text-nav-container .inner-wrap.clearfix #menu-menu-1 li a")
        for m in menu[1:]:
            category1_url.append(m.get("href"))
        for c1 in category1_url:
            yield scrapy.Request(c1, callback=self.parse_category1)

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        news_content = soup.select("#content .article-container article div .entry-content.clearfix a")
        meta = {'category1':soup.select_one("header.page-header h1 span").text.strip()}
        for n in news_content:
            news_url.append(n.get("href"))
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_detail, meta=meta)
        next_page = soup.select_one("#content .content a").get("href") if soup.select_one(
            "#content .content a") else None
        LastTimeStamp = lastestnews1_time_switch1(soup.select(".article-container article")[-1].select_one(".posted-on .entry-date.published").get("datetime"))
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
        if soup.select(".error404"):
            self.logger.info("该页面404")
            return
        else:
            item['category1'] = response.meta['category1']
            item['category2'] = None
            item['title'] = soup.select_one("#content .entry-header h1").text.strip()
            item['pub_time'] = lastestnews1_time_switch2(soup.select_one(".below-entry-meta .posted-on time").get("datetime"))
            body_list = soup.select(".entry-content.clearfix p") if soup.select(".entry-content.clearfix p") else None
            if body_list is not None:
                item['abstract'] = body_list[0].text.strip()
                body = ""
                for b in body_list:
                    body += b.text.strip() + "\n"
                item['body'] = body
            else:
                body_string = soup.select_one("#content article div .entry-content.clearfix").text.strip()
                if re.match(r"Share\n\n\n\n\n\n+\S+\n\n\n\n\n\nLinkedIn", body_string):
                    body = ""
                    item['body'] = item['abstract'] = re.findall("LinkedIn(.*?)Share", body_string, re.S)[0]
                else:
                    item['body'] = item['abstract'] = body_string
            image = soup.select(".entry-content.clearfix .wp-block-image img")
            images = []
            for img in image:
                images.append(img.get("src"))
            item['images'] = images
            item['website_id'] = self.website_id
            item['language_id'] = self.language_id
            item['request_url'] = response.request.url
            item['response_url'] = response.url
            item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
=======
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime

def lastestnews1_time_switch1(time_string):
    # 2020-12-23T17:50:27+05:30
    # 返回时间戳
    time_string = time_string.rsplit("+", 1)[0]
    return Util.format_time3(str(datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")))

def lastestnews1_time_switch2(time_string):
    # 2020-12-23T17:50:27+05:30
    # 返回%Y-%m-%d %H:%M:%S
    time_string = time_string.rsplit("+", 1)[0]
    return datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")

# 将爬虫类名和name字段改成对应的网站名
class Latestnews1Spider(scrapy.Spider):
    name = 'latestnews1'
    website_id = 936  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.latestnews1.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(Latestnews1Spider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = int(time) if time is not None else time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category1_url = []
        menu = soup.select("#header-text-nav-container .inner-wrap.clearfix #menu-menu-1 li a")
        for m in menu[1:]:
            category1_url.append(m.get("href"))
        for c1 in category1_url:
            yield scrapy.Request(c1, callback=self.parse_category1)

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        news_content = soup.select("#content .article-container article div .entry-content.clearfix a")
        meta = {'category1':soup.select_one("header.page-header h1 span").text.strip()}
        for n in news_content:
            news_url.append(n.get("href"))
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_detail, meta=meta)
        next_page = soup.select("#content .previous a")[0].attrs['href'] if soup.select("#content .previous a") else None
        LastTimeStamp = lastestnews1_time_switch1(soup.select(".article-container article")[-1].select_one(".posted-on .entry-date.published").get("datetime"))
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
        if soup.select(".error404"):
            self.logger.info("该页面404")
            return
        else:
            item['category1'] = response.meta['category1']
            item['category2'] = None
            item['title'] = soup.select_one("#content .entry-header h1").text.strip()
            item['pub_time'] = lastestnews1_time_switch2(soup.select_one(".below-entry-meta .posted-on time").get("datetime"))
            body_list = soup.select(".entry-content.clearfix p") if soup.select(".entry-content.clearfix p") else None
            if body_list is not None:
                item['abstract'] = body_list[0].text.strip()
                body = ""
                for b in body_list:
                    body += b.text.strip() + "\n"
                item['body'] = body
            else:
                body_string = soup.select_one("#content article div .entry-content.clearfix").text.strip()
                if re.match(r"Share\n\n\n\n\n\n+\S+\n\n\n\n\n\nLinkedIn", body_string):
                    body = ""
                    item['body'] = item['abstract'] = re.findall("LinkedIn(.*?)Share", body_string, re.S)[0]
                else:
                    item['body'] = item['abstract'] = body_string
            image = soup.select(".entry-content.clearfix .wp-block-image img")
            images = []
            for img in image:
                images.append(img.get("src"))
            item['images'] = images
            item['website_id'] = self.website_id
            item['language_id'] = self.language_id
            item['request_url'] = response.request.url
            item['response_url'] = response.url
            item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
>>>>>>> master:demo/已部署/latestnews1.py
            yield item