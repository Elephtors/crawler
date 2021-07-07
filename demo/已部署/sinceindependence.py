# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime


def sinceindependece_time_switch1(time_string):
    # 返回时间戳
    #  जनवरी 3, 2021
    Hindi_month = {
        "जनवरी": 1, "फ़रवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6, "जुलाई": 7,
        "अगस्त": 8, "सितंबर": 9, "अक्टूबर": 10, "नवंबर": 11, "दिसंबर": 12, "सितम्बर": 9
    }
    time_list = re.split(" |,", time_string)
    month = int(Hindi_month[time_list[1]])
    day = int(time_list[2])
    year = int(time_list[-1])
    data = time.strftime("%Y-%m-%d %H:%M:%S", datetime(year, month, day).timetuple())
    timeArray = time.strptime(data, "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp


def sinceindependece_time_switch2(time_string):
    # 返回 %Y-%m-%d %H:%M:%S
    # 01/3/21 12:20 अपराह्न
    Hindi_month = {
        "जनवरी": 1, "फ़रवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6, "जुलाई": 7,
        "अगस्त": 8, "सितंबर": 9, "अक्टूबर": 10, "नवंबर": 11, "दिसंबर": 12
    }
    time_list = re.split("/| |:", time_string)
    month, day, year, hour, minute, sth = re.split("/| |:", time_string)
    return datetime.strptime(("%s-%s-%s %s:%s:00" % (year, month, day, hour, minute)), "%y-%m-%d %H:%M:00")

def IfFollowAdExist(body_string):
    # 判断body结尾是否有关注广告，有则去除
    mx1 = "Like and Follow us on :"
    mx2 = "Twitter\nFacebook\nInstagram\nYouTube"
    mx1_result = "(.*?)Like and Follow us on :"
    mx2_result = "(.*?)Twitter"
    if re.findall(mx1, body_string, re.S):
        return re.findall(mx1_result, body_string, re.S)
    elif re.findall(mx2, body_string, re.S):
        return re.findall(mx2_result, body_string, re.S)
    else:
        return body_string


# 将爬虫类名和name字段改成对应的网站名
class SinceindependenceSpider(scrapy.Spider):
    name = 'sinceindependence'
    website_id = 925  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://hindi.sinceindependence.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(SinceindependenceSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        menu = soup.find("div", class_="jeg_header normal").find("div",
                                                                 class_="jeg_bottombar jeg_navbar jeg_container "
                                                                        "jeg_navbar_wrapper jeg_navbar_normal "
                                                                        "jeg_navbar_normal").find(
            "div", class_="jeg_nav_col jeg_nav_center jeg_nav_grow").find("ul")
        zz = '<li class="menu-item menu-item-type-taxonomy.*?"><a href="(.*?)">'
        category1_list = re.findall(zz, str(menu), re.S)
        for c1 in category1_list[0:11]:
            yield scrapy.Request(c1, callback=self.parse_category1)

    def parse_category1(self, response):
        # 获取当前页新闻链接
        soup = BeautifulSoup(response.text, features="lxml")
        news_list = soup.select(".jnews_category_content_wrapper .jeg_block_container article")
        news_url = []
        for n in news_list:
            url = n.find("div", class_="jeg_thumb").find("a").get("href")
            news_url.append(url)
        for url in news_url:
            yield scrapy.Request(url, callback=self.parse_detail)

        # 判断时间戳 时间截止
        date = soup.select(".jnews_category_content_wrapper .jeg_block_container article")[-1].find("div",
                                                                                                    class_="jeg_meta_date").text
        timestamp = sinceindependece_time_switch1(date)
        next_button = soup.select_one(".jeg_block_navigation").find("a", class_="page_nav next") if soup.select_one(
            ".jeg_block_navigation").find("a", class_="page_nav next") else None  # next按钮
        next_url = next_button.get("href") if next_button else None
        if self.time is None:
            yield scrapy.Request(next_url, callback=self.parse_category1)
        elif self.time and timestamp >= int(self.time) and next_button:
            yield scrapy.Request(next_url, callback=self.parse_category1)
        else:
            self.logger.info("时间截止")

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features="lxml")
        item['title'] = soup.select_one(".entry-header .jeg_post_title").text \
            if soup.select_one(".entry-header .jeg_post_title") else None
        item['abstract'] = soup.select_one(".entry-header .jeg_post_subtitle").text \
            if soup.select_one(".entry-header .jeg_post_subtitle") else None
        item['pub_time'] = sinceindependece_time_switch2(
            soup.select_one(".jeg_meta_container .jeg_meta_date").text.strip())
        images = []
        img = soup.find("div", class_="jeg_featured featured_image").\
            find("div", class_="thumbnail-container animate-lazy").find_all("img") \
            if soup.find("div", class_="jeg_featured featured_image") else None
        for i in img:
            images.append(i.get("data-src"))
        item['images'] = images
        body = ""
        for b in soup.select_one(".content-inner ").find_all("p"):
            body += b.text.strip()
            body += "\n"
        item['body'] = IfFollowAdExist(body)
        item['request_url'] = response.request.url
        item['response_url'] = response.url
        item['category1'] = soup.select_one("#breadcrumbs .breadcrumb_last_link").text.strip() if soup.select_one(
            "#breadcrumbs .breadcrumb_last_link") else None
        item['category2'] = None
        item['website_id'] = self.website_id
        item['language_id'] = self.language_id
        item['cole_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
        yield item
