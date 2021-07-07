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


def tv9hindi_time_switch2(time_string):
    # 返回 %Y-%m-%d %H:%M:%S
    # Publish Date -\n\t\t3:49 am, Thu, 7 January 21
    return datetime.strptime(time_string, "Publish Date -\n\t\t%H:%M %p, %a, %d %B %y")
    pass


# 将爬虫类名和name字段改成对应的网站名
class Tv9hindiSpider(scrapy.Spider):
    name = 'tv9hindi'
    website_id = 923  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.tv9hindi.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(Tv9hindiSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category1_url = []
        category_topic = soup.find("div", class_="top9MenuBox flex").select_one(".top9MenuLink").find_all("a")
        category_topic_first = category_topic[0]
        category_topic = category_topic[2:]
        category_topic.append(category_topic_first)
        category_trend = soup.find("div", class_="TrendStrip flex").select_one(".TrendStripLink").find_all("a")
        for category in category_topic:
            category1_url.append(category.get("href"))
        for category in category_trend:
            category1_url.append(category.get("href"))
        for c1 in category1_url:
            yield scrapy.Request('https://www.tv9hindi.com' + c1, callback=self.parse_category1) if c1[0] == '/' else scrapy.Request(
                c1, callback=self.parse_category1)

    def parse_category1(self, response):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(response.text, features="lxml")
        news_url = []
        if re.match(r"\S+/page/\d+$", response.url):
            # https://www.tv9hindi.com/india/page/2
            news_content = soup.find_all("div", class_="newsTop9")[-1].find("div", class_="col2 ComListing").select(
                "li h3 a")
            for li in news_content:
                news_url.append(li.get("href"))
        else:
            top_content = soup.select_one(".newsTop9  .topNewscomp ul").find_all("h3", class_="h3")
            for h3 in top_content:
                news_url.append(h3.find("a").get("href"))
            news_content = soup.find_all("div", class_="newsTop9")[-1].find("div", class_="col2 ComListing").select(
                "li h3 a") if soup.find_all("div", class_="newsTop9")[-1].find("div", class_="col2 ComListing") else None
            for li in news_content:
                news_url.append(li.get("href"))
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_detail)
        last_timeStamp = Util.format_time3(Util.format_time2(soup.find_all("div", class_="col2 ComListing")[-1].find_all("div", class_="catTime flex")[-1].find("span").text.strip()))
        next_page = soup.find("a", class_="next page-numbers").get("href") if soup.find("a",
                                                                                        class_="next page-numbers") else None
        pattern_pingback = '<!--<link rel="pingback" href="https://www.tv9hindi.com/xmlrpc.php">-->'  # 判断是否到达最后一页
        next_soup = BeautifulSoup(requests.get(next_page).text, features="lxml")
        if next_page:
            if self.time is None:
                if int(next_page.rsplit("/", 1)[-1]) <= 50:
                    yield scrapy.Request(next_page, callback=self.parse_category1)
                else:
                    pass
            elif last_timeStamp >= int(self.time):
                yield scrapy.Request(next_page, callback=self.parse_category1)
            else:
                self.logger.info("时间截止")
        else:
            self.logger.info("该目录已经结束")

    def parse_detail(self, response):
        item = DemoItem()
        soup = soup = BeautifulSoup(response.text, features="lxml")
        item['title'] = soup.select_one(".detailBody").find("div", class_="LeftCont content").find(
            "h1").text.strip() if soup.select_one(".detailBody") else None
        images = []
        image = soup.select_one(".ArticleBodyCont .articleImg").find_all("img") if soup.select_one(
            ".ArticleBodyCont .articleImg") else None
        for img in image:
            images.append(img.get("data-src"))
        item['images'] = images
        pub_time = soup.find("div", class_="LeftCont content").find("ul", class_="AuthorInfo").find_all("li")[
            -1].text.strip() if soup.find("div", class_="LeftCont content") else None
        item['pub_time'] = tv9hindi_time_switch2(pub_time)
        item['abstract'] = soup.find("div", class_="LeftCont content").find_all("p")[1].text.strip() if soup.find("div",
                                                                                                                  class_="LeftCont content") else None
        body_content = soup.find("div", class_="ArticleBodyCont").find_all("p") if soup.find("div", class_="ArticleBodyCont") else None
        body = ""
        mx = '<p><span style="color: #0000ff;">'  # 过滤
        for p in body_content:
            if re.match(mx, str(p)) is None:
                body += p.text.strip()
                body += "\n"
            else:
                pass
        category = soup.find("div", class_="breadcrum").select_one("#breadcrumbs").find_all("a")[-2:] if soup.find("div", class_="breadcrum") else None
        item['category1'] = category[0].text.strip()
        item['category2'] = category[1].text.strip()
        item['body'] = body
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        yield item
