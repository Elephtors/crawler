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
class politicsSpider(scrapy.Spider):
    name = 'politics'
    website_id = 1206 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://politics.com.ph/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(politicsSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        temp = soup.select_one("nav>div.wrapper") if soup.select_one("nav>div.wrapper") else None
        a_list = temp.select("a") if temp and temp.select("a") else []
        for a in a_list[0:6]:
            url = a.get("href") if a.get("href") else None
            if url:
                yield scrapy.Request(url, callback=self.parse_news_list)

    def parse_news_list(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        temp_list = soup.select("header.entry-header") if soup.select("header.entry-header") else []
        for temp in temp_list:
            url = temp.find("a").get("href") if temp.find("a").get("href") else None
            if url:
                yield scrapy.Request(url, callback=self.parse_news)
        # 翻页
        temp2 = soup.find_all("time", class_="entry-date published") if soup.find_all("time", class_="entry-date published") else None
        pub_time = temp2[-1].get("datetime") if temp2 and temp2[-1].get("datetime") else None
        pub_time_list = re.split("T|\+", pub_time) if pub_time else None
        time = pub_time_list[0]+" "+pub_time_list[1] if pub_time_list and len(pub_time_list) >= 2 else None
        temp3 = soup.find("a", class_="next page-numbers") if soup.find("a", class_="next page-numbers") else None
        next_page = temp3.get("href") if temp3 and temp3.get("href") else None
        if time:
            if self.time == None or Util.format_time3(time) >= int(self.time):
                if next_page:
                    yield scrapy.Request(next_page, callback=self.parse_news_list)
            else:
                self.logger.info('时间截止')

    def parse_news(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, "html.parser")
        images = []
        temp = soup.select_one("div.relative") if soup.select_one("div.relative") else None
        image = temp.get("style").split("'")[-2] if temp and temp.get("style").split("'")[-2] else None
        if image:
            images.append(image)
        item["images"] = images
        temp_list = soup.find_all("span", {"itemprop": "name"}) if soup.find_all("span", {"itemprop": "name"}) else []
        item["category1"] = temp_list[1].text.strip() if len(temp_list) >= 3 else None
        item["category2"] = ''
        item["title"] = temp_list[2].text.strip() if len(temp_list) >= 3 else None
        if soup.find("time", class_="entry-date published"):
            temp2 = soup.find("time", class_="entry-date published")
        elif soup.find("time", class_="entry-date published updated"):
            temp2 = soup.find("time", class_="entry-date published updated")
        else:
            temp2 = None
        time = temp2.get("datetime") if temp2 and temp2.get("datetime") else None
        pub_time_list = re.split("T|\+", time) if time else None
        item["pub_time"] = pub_time_list[0] + " " + pub_time_list[1] if pub_time_list and len(pub_time_list) >= 2 else None
        body = []
        body_list = soup.select("div.entry-content>p") if soup.select("div.entry-content>p") else []
        for b in body_list[1:]:
            if b.text.strip():
                body.append(b.text.strip())
        item["abstract"] = body[0] if body else None
        item["body"] = '\n'.join(body) if body else None
        if body:
            yield item