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
class dfaSpider(scrapy.Spider):
    name = 'dfa'
    website_id = 1216 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://dfa.gov.ph/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(dfaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        soup = BeautifulSoup(response.text, "html.parser")
        meta["pub_time"] = None
        meta["category1"] = 'News'
        a_list = soup.find("li", class_="item-1048 deeper parent gmenu").select("ul>li>a")
        for a in a_list:
            if a.get("href") != "/":
                if a.text.strip() == "DFA Releases":
                    meta["category2"] = "DFA Releases"
                elif a.text.strip() == "Statements and Advisories":
                    meta["category2"] = "Statements and Advisories"
                elif a.text.strip() == "News from our Foreign Service Posts":
                    meta["category2"] = "News from our Foreign Service Posts"
                else:
                    meta["category2"] = "Events"
                url = "https://dfa.gov.ph" + a.get("href")
                yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)
        meta["category1"] = 'Gender and Development'
        meta["category2"] = None
        url = "https://dfa.gov.ph/gad-feature-news"
        yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)
        meta["category1"] = 'COVID-19 Advisories'
        meta["category2"] = None
        url = "https://dfa.gov.ph" + soup.find("li", class_="item-1130 gmenu").select_one("a").get("href")
        yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)

    def parse_news_list(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = soup.select("tbody>tr") if soup.select("tbody>tr") else []
        time2 = None
        for news in news_list:
            url = "https://dfa.gov.ph" + news.select_one("a").get("href")
            pub_time_list = news.find("td", class_="list-date small").text.strip().split(" ") if news.find("td", class_="list-date small") else None
            if pub_time_list:
                if pub_time_list[1] == "January":
                    time2 = pub_time_list[2] + "-01-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "February":
                    time2 = pub_time_list[2] + "-02-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "March":
                    time2 = pub_time_list[2] + "-03-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "April":
                    time2 = pub_time_list[2] + "-04-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "May":
                    time2 = pub_time_list[2] + "-05-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "June":
                    time2 = pub_time_list[2] + "-06-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "July":
                    time2 = pub_time_list[2] + "-07-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "August":
                    time2 = pub_time_list[2] + "-08-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "September":
                    time2 = pub_time_list[2] + "-09-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "October":
                    time2 = pub_time_list[2] + "-10-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "November":
                    time2 = pub_time_list[2] + "-11-" + pub_time_list[0] + " 00:00:00"
                elif pub_time_list[1] == "December":
                    time2 = pub_time_list[2] + "-12-" + pub_time_list[0] + " 00:00:00"
            response.meta["pub_time"] = time2
            yield scrapy.Request(url, meta=response.meta, callback=self.parse_news)
        next_page = "https://dfa.gov.ph" + soup.select_one("li.pagination-next>a").get("href") if soup.select_one("li.pagination-next>a") else None
        if self.time == None or (time2 and Util.format_time3(time2) >= int(self.time)):
            if next_page:
                yield scrapy.Request(next_page, meta=response.meta, callback=self.parse_news_list)
        else:
            self.logger.info('时间截止')

    def parse_news(self, response):
        item = DemoItem()
        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        item["pub_time"] = response.meta["pub_time"] if response.meta["pub_time"] != None else Util.format_time()
        soup = BeautifulSoup(response.text, "html.parser")
        temp = soup.find("div", {"itemprop": "articleBody"}) if soup.find("div", {"itemprop": "articleBody"}) else None
        item["title"] = soup.select('h1.entry-title')[0].text
        body = []
        temp2_list = temp.find_all("p", {"style": "text-align: justify;"}) if temp.find_all("p", {"style": "text-align: justify;"}) else []
        for temp2 in temp2_list:
            [s.extract() for s in temp2('script')]
            b = temp2.get_text().strip().split('\xa0') if temp2.text else None
            b = ' '.join(b) if b else None
            if b:
                body.append(b)
        item["abstract"] = body[0] if body else None
        item["body"] = '\n'.join(body) if body else None
        images = []
        temp3_list = temp.find_all("p", {"style": "text-align: center;"}) if temp and temp.find_all("p", {"style": "text-align: center;"}) else []
        for temp3 in temp3_list:
            image = "https://dfa.gov.ph" + temp3.find("img").get("src") if temp3.find("img") and temp3.find("img").get("src") else None
            if image:
                images.append(image)
        item["images"] = images
        yield item
