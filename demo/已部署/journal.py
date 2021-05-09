import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time


class JournalSpider(scrapy.Spider):
    name = 'journal'
    allowed_domains = ['journal.com.ph']
    website_id = 196  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    start_urls = ['https://journal.com.ph/news/',
                  'https://journal.com.ph/sports/',
                  'https://journal.com.ph/entertainment/',
                  'https://journal.com.ph/technology/',
                  'https://journal.com.ph/lifestyle/',
                  'https://journal.com.ph/editorial/',
                  'https://journal.com.ph/specials/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(JournalSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        meta = {}
        soup = bs(response.text,"html.parser")
        for i in soup.select("#site-navigation > div > ul > li"):
            if i.find("a").text == soup.find(class_="page-title mt-archive-title").text:
                meta["category1"] = soup.find(class_="page-title mt-archive-title").text
                for li in i.select("ul > li"):
                    url = li.find("a").get("href")
                    meta["category2"] = li.find("a").text
                    yield scrapy.Request(url,callback=self.parse2,meta=meta)

    def parse2(self,response):
        soup = bs(response.text,"html.parser")
        for i in soup.find_all(class_="entry-title"):
            news_url = i.find("a").get("href")
            yield scrapy.Request(news_url,callback=self.parse_news,meta=response.meta)

        pub = soup.select(".posted-on > a > time")[-1].text
        if self.time == None or Util.format_time3(Util.format_time2(pub)) >= int(self.time):
            url = soup.select(".nav-links > a")[-1].get("href")
            yield Request(url,callback=self.parse2,meta=response.meta)
        else:
            self.logger.info('时间截止')

    def parse_news(self,response):
        item = DemoItem()
        soup = bs(response.text,"html.parser")

        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]

        title = soup.find(class_="entry-title").text.strip()
        item["title"] = title
        pub_time = soup.select_one(".posted-on > a > time").text
        item["pub_time"] = Util.format_time2(pub_time)
        images = []
        if soup.find(class_="single-post-image").find("img"):
            images = [soup.find(class_="single-post-image").find("img").get("src")]
        if soup.find(class_="entry-content").find_all("img"):
            for img in soup.find(class_="entry-content").find_all("img"):
                images.append(img.get("src"))
        item["images"] = images
        abstract = soup.find(class_="entry-content").find("h2").text if soup.find(class_="entry-content").find("h2") else soup.find(class_="entry-content").find("p").text
        item["abstract"] = abstract
        body = ''
        for p in soup.find(class_="entry-content").find_all("p"):
            body += (p.text + '\n')
        item["body"] = body
        self.logger.info(item)
        self.logger.info('\n')
        yield item




