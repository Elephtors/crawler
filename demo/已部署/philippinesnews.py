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
class philippinesnewsSpider(scrapy.Spider):
    name = 'philippinesnews'
    website_id = 1209 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.philippinesnews.net/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(philippinesnewsSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta["category1"] = None
        meta["category2"] = None
        soup = BeautifulSoup(response.text, "html.parser")
        temp_list = soup.find("ul", class_="dropdown menu").select("li a")
        for temp in temp_list[1:4]:
            url = "https://www.philippinesnews.net" + temp.get("href")
            meta["category1"] = temp.text.strip()
            yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)

    def parse_news_list(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        temp_list = soup.select("div.media-object-section h5")
        for temp in temp_list:
            url = "https://www.philippinesnews.net" + temp.find("a").get("href")
            yield scrapy.Request(url, meta=response.meta, callback=self.parse_news)

    def parse_news(self, response):
        item = DemoItem()
        try:
            item["category1"] = response.meta["category1"]
            item["category2"] = response.meta["category2"]
            response1 = response.text.replace('<br>', ' ')
            soup = BeautifulSoup(response1, "html.parser")
            # 时间
            temp = soup.select_one("div.title_text") if soup.select_one("div.title_text") else None
            pub_time_list = re.split(" |,", temp.select_one("p").text) if temp.select_one("p").text else None
            if pub_time_list:
                if pub_time_list[-5] == "Jan":
                    time = pub_time_list[-4]+"-01-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Feb":
                    time = pub_time_list[-4]+"-02-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Mar":
                    time = pub_time_list[-4]+"-03-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Apr":
                    time = pub_time_list[-4]+"-04-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "May":
                    time = pub_time_list[-4]+"-05-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Jun":
                    time = pub_time_list[-4]+"-06-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Jul":
                    time = pub_time_list[-4]+"-07-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Aug":
                    time = pub_time_list[-4]+"-08-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Sept":
                    time = pub_time_list[-4]+"-09-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Oct":
                    time = pub_time_list[-4]+"-10-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Nov":
                    time = pub_time_list[-4]+"-11-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                elif pub_time_list[-5] == "Dec":
                    time = pub_time_list[-4]+"-12-"+pub_time_list[-6]+" "+pub_time_list[-2]+":00"
                item["pub_time"] = time
            else:
                item["pub_time"] = None
            # 标题
            item["title"] = temp.find("a").text.strip() if temp.find("a").text else None
            # 摘要和正文
            body = []
            temp_list = soup.select_one("div.detail_text").find_all("p") if soup.select_one("div.detail_text").find_all("p") else None
            if temp_list:
                for temp in temp_list:
                    body.append(temp.text.strip())
                item["abstract"] = body[0]
                item["body"] = "\n".join(body)
            else:
                item["abstract"] = None
                item["body"] = None
            # 图片
            images = []
            image_list = soup.select("div.article_image") if soup.select("div.article_image") else None
            if image_list:
                for image in image_list:
                    images.append(image.find("img").get("src"))
            item["images"] = images
        except Exception:
            pass
        yield item