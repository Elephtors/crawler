import json
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#将爬虫类名和name字段改成对应的网站名
class philboxingSpider(scrapy.Spider):
    name = 'philboxing'
    website_id = 1194 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['http://philboxing.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(philboxingSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        soup = BeautifulSoup(response.text, "html.parser")
        url = soup.select_one("a.sidenav").get("href")
        meta["category1"] = soup.select_one("a.sidenav").text.strip()
        meta["category2"] = ''
        meta["abstract"] = ''
        yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)

    def parse_news_list(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        # 每页第一条新闻
        web = soup.find("td", {"valign": "top"}).select_one("td>font>a").text.strip() if soup.find("td", {"valign": "top"}).select_one("td>font>a").text else None
        if web and web == "PhilBoxing.com":
            url = soup.find("td", {"valign": "top"}).select_one("td>a").get("href") if soup.find("td", {"valign": "top"}).select_one("td>a").get("href") else None
            abstract = soup.find("td", {"valign": "top"}).select_one("td>font.newsblurb").text.strip().split("\r\n\r\n") if soup.find("td", {"valign": "top"}).select_one("td>font.newsblurb").text else None
            response.meta["abstract"] = ' '.join(abstract) if abstract else None
            if url:
                yield scrapy.Request(url, meta=response.meta, callback=self.parse_news)
        # 除第一条新闻的其他新闻
        table = soup.find("table", {"width": "100%", "height": "100%"}) if soup.find("table", {"width": "100%", "height": "100%"}) else None
        p = table.select("p")[2] if table and table.select("p")[2] else None
        web_list = p.select("p>font>a") if p and p.select("p>font>a") else None
        news_list = p.select("p>a") if p and p.select("p>a") else None
        abstract_list = p.select("p>font.newsblurb") if p and p.select("p>font.newsblurb") else None
        i = 0
        if web_list:
            for web in web_list:
                if web.text.strip() == "PhilBoxing.com":
                    url = news_list[2*i].get("href") if news_list and news_list[2*i].get("href") else None
                    abstract = abstract_list[i].text.strip().split("\r\n\r\n") if abstract_list and abstract_list[i].text else None
                    response.meta["abstract"] = ' '.join(abstract) if abstract else None
                    if url:
                        yield scrapy.Request(url, meta=response.meta, callback=self.parse_news)
                    i += 1
                else:
                    i += 1
        # 翻页
        time_list = p.find_all("font", {"size": "2"})[-1].text.split(" ")
        if time_list:
            if time_list[-2] == "Jan":
                time = time_list[-1]+"-01-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Feb":
                time = time_list[-1]+"-02-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Mar":
                time = time_list[-1]+"-03-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Apr":
                time = time_list[-1]+"-04-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "May":
                time = time_list[-1]+"-05-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Jun":
                time = time_list[-1]+"-06-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Jul":
                time = time_list[-1]+"-07-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Aug":
                time = time_list[-1]+"-08-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Sept":
                time = time_list[-1]+"-09-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Oct":
                time = time_list[-1]+"-10-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Nov":
                time = time_list[-1]+"-11-"+time_list[-3]+" 00:00:00"
            elif time_list[-2] == "Dec":
                time = time_list[-1]+"-12-"+time_list[-3]+" 00:00:00"
            else:
                time = None
            if time and (self.time == None or Util.format_time3(time) >= int(self.time)):
                font_list = soup.select("font.boxertablebody") if soup.select("font.boxertablebody") else None
                a_list = font_list[-1].select("a") if font_list and font_list[-1].select("a") else None
                next_page = "http://philboxing.com/news/" + a_list[0].get("href") if a_list and a_list[0].get("href") else None
                if next_page:
                    yield scrapy.Request(next_page, meta=response.meta, callback=self.parse_news_list)
            else:
                self.logger.info('时间截止')

    def parse_news(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, "html.parser")
        # 目录和摘要
        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        item["abstract"] = response.meta["abstract"]
        # 标题
        item["title"] = soup.select_one("font.storytitle").text.strip() if soup.select_one("font.storytitle").text else None
        # 时间
        pub_time_list = soup.select_one("font.storydate").text.split(" ") if soup.select_one("font.storydate").text else None
        if pub_time_list:
            if pub_time_list[-2] == "Jan":
                time = pub_time_list[-1]+"-01-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Feb":
                time = pub_time_list[-1]+"-02-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Mar":
                time = pub_time_list[-1]+"-03-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Apr":
                time = pub_time_list[-1]+"-04-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "May":
                time = pub_time_list[-1]+"-05-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Jun":
                time = pub_time_list[-1]+"-06-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Jul":
                time = pub_time_list[-1]+"-07-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Aug":
                time = pub_time_list[-1]+"-08-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Sept":
                time = pub_time_list[-1]+"-09-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Oct":
                time = pub_time_list[-1]+"-10-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Nov":
                time = pub_time_list[-1]+"-11-"+pub_time_list[-3]+" 00:00:00"
            elif pub_time_list[-2] == "Dec":
                time = pub_time_list[-1]+"-12-"+pub_time_list[-3]+" 00:00:00"
            item["pub_time"] = time
        else:
            item["pub_time"] = None
        # 正文
        body = []
        body_list = soup.select_one("font.storycontent").text.split("\r") if soup.select_one("font.storycontent").text else None
        if body_list:
            for b in body_list:
                body.append(b.strip())
        item["body"] = '\n'.join(body) if body else None
        # 图片
        img_list = []
        images_list = soup.select("font.storycontent>img") if soup.select("font.storycontent>img") else None
        if images_list:
            for images in images_list:
                image = images.get("src")
                img_list.append(image)
        item["images"] = img_list
        yield item