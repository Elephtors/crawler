import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time
from urllib import parse

class BicolstandardSpider(scrapy.Spider):
    name = 'bicolstandard'
    allowed_domains = ['www.bicolstandard.com']
    website_id = 491  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    start_urls = ['http://www.bicolstandard.com/']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(BicolstandardSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        soup = bs(response.text,"html.parser")
        for li in soup.select("#menu-main-nav > li"):
            if li.find("a").text != 'Advertise':
                category1 = li.find("a").text
                category2 = None
                url = li.find("a").get("href")
                yield scrapy.Request(url,callback=self.parse_page,meta={"category1":category1,"category2":category2,"p":1,"url":url})

    def parse_page(self,response):
        soup = bs(response.text,"html.parser")
        if soup.find(class_="post-outer") != None:
            for i in soup.find_all(class_="post-title entry-title"):
                news_url = i.find("a").get("href")
                yield scrapy.Request(news_url,callback=self.parse_news,meta=response.meta)

            pub = soup.find_all(class_="published timeago")[-1].text.strip()
            time = parse.quote(soup.find_all(class_="published timeago")[-1].get("title"))
            # page = soup.select_one("div.blog-pager > span.showpageOf").text #.split("of")[-1].strip()
            # self.logger.info(page)
            if self.time == None or Util.format_time3(Util.format_time2(pub)) >= int(self.time):
                url = response.meta["url"] + "?updated-max={}&max-results=8#PageNo={}"
                response.meta["p"] += 1
                yield scrapy.Request(url.format(time,response.meta["p"]),callback=self.parse_page,meta=response.meta)
            else:
                self.logger.info('时间截止')

    def parse_news(self,response):
        item = DemoItem()
        soup = bs(response.text,"html.parser")
        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]

        item["title"] = soup.find(class_="post-title entry-title").text.strip()
        item["pub_time"] = Util.format_time2(soup.find(class_="published timeago").text.strip())

        content = soup.find(class_="post-body entry-content")
        images = [img.get("src") for img in content.find_all("img")] if content.find_all("img") else []
        item["images"] = images
        body1 = ''
        for div in content.find_all(dir="ltr"):
            body1 += (div.text.strip() + '\n')
        if body1 == '':
            body1 = content.text

        body = ''
        for b in body1.split("\n"):
            if b != '':
                body += (b + '\n')
        item["body"] = body
        item["abstract"] = body.split("\n")[0]
        yield item
