# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
from datetime import datetime

def headlinehindi_time_switch1(time_string):
    # 2020-12-23T17:50:27+05:30
    # 返回时间戳
    time_string = time_string.rsplit("+", 1)[0]
    return Util.format_time3(str(datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")))

def headlinehindi_time_switch2(time_string):
    # 2020-12-26T18:10:41+05:30
    # 返回%Y-%m-%d %H:%M:%S
    time_string = time_string.rsplit("+", 1)[0]
    return datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")


# 将爬虫类名和name字段改成对应的网站名
class HeadlinehindiSpider(scrapy.Spider):
    name = 'headlinehindi'
    website_id = 932  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.headlinehindi.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(HeadlinehindiSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = int(time) if time is not None else time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category1_url = []
        menu = soup.select(
            "#td-outer-wrap .td-header-template-wrap .td-header-desktop-wrap .wpb_wrapper .wpb_wrapper div div "
            "#menu-td-demo-header-menu li a")
        for a in menu:
            category1_url.append(a.get("href"))
        for c1 in category1_url:
            yield scrapy.Request(c1, callback=self.parse_category1)

    def parse_category1(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        news_content = soup.select_one("#td-outer-wrap .tdc-content-wrap").find_all("div", class_="tdb_module_loop td_module_wrap td-animation-stack")
        for n in news_content:
            news_url.append(n.select_one(".td-module-meta-info h3 a").get("href"))
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_detail)
        next_page = soup.find("div", class_="page-nav td-pb-padding-side").find_all("a")[-1].get("href")
        LastTimeStamp = headlinehindi_time_switch1(news_content[-1].select_one(".td-editor-date span time").get("datetime"))
        if self.time is None or LastTimeStamp >= self.time:
            if next_page:
                yield scrapy.Request(next_page, callback=self.parse_category1)
            else:
                self.logger.info("该页到底")
        else:
            self.logger.info("时间截止")

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features="lxml")
        item['title'] = soup.select_one(".wpb_wrapper div div h1").text.strip()
        item['pub_time'] = headlinehindi_time_switch2(soup.select_one(".wpb_wrapper div div time").get("datetime"))
        images = [soup.select_one(".wpb_wrapper div div .td-modal-image").get("data-src")] if soup.select_one(".wpb_wrapper div div .td-modal-image") else []
        item['images'] = images
        body = ""
        body_content = soup.select(".wpb_wrapper div.tdb-block-inner.td-fix-index p")
        for b in body_content:
            body += b.text.strip()+"\n"
        item['body'] = body
        item['abstract'] = body
        item['category1'] = soup.select(".wpb_wrapper div.tdb-block-inner.td-fix-index span a")[1].text.strip()
        item['category2'] = None
        yield item



