import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time

class BusinessmirrorSpider(scrapy.Spider):
    name = 'businessmirror'
    allowed_domains = ['businessmirror.com.ph']
    website_id = 188  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    start_urls = ['https://businessmirror.com.ph/category/news/',
                  'https://businessmirror.com.ph/category/business/',
                  'https://businessmirror.com.ph/category/sports/',
                  'https://businessmirror.com.ph/category/opinion/',
                  'https://businessmirror.com.ph/category/life/',
                  'https://businessmirror.com.ph/category/features/',
                  'https://businessmirror.com.ph/category/bmplus/',
                  'https://businessmirror.com.ph/category/covid-19/',
                  'https://businessmirror.com.ph/category/the-broader-look/']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(BusinessmirrorSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        meta = {}
        soup = bs(response.text,"html.parser")

        category1 = soup.find(class_="tdb-title-text").text.strip()
        meta["category1"] = category1
        for i in soup.find_all(class_="td-module-container td-category-pos-above"):
            news_url = i.find(class_="entry-title td-module-title").find("a").get("href")
            category2 = i.find(class_="td-module-meta-info").select_one("a").text.strip()
            if category2 == category1:
                category2 = None
            meta["category2"] = category2
            yield scrapy.Request(news_url,callback=self.parse_news,meta=meta)

        pub = soup.find_all(class_="entry-date updated td-module-date")[-1].text.strip()
        if self.time == None or Util.format_time3(Util.format_time2(pub)) >= int(self.time):
            url = soup.find("div","page-nav td-pb-padding-side").select("a")[-1].get("href")
            yield Request(url,callback=self.parse)
        else:
            self.logger.info('时间截止')

    def parse_news(self,response):
        item = DemoItem()
        soup = bs(response.text,"html.parser")

        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]

        title = soup.find(class_="tdb-title-text").text.strip()
        item["title"] = title
        pub_time = soup.find(class_="entry-date updated td-module-date").text.strip()
        item["pub_time"] = Util.format_time2(pub_time)
        images = [soup.find("div","tdb-block-inner td-fix-index").find("img").get("src")] if soup.find("div","tdb-block-inner td-fix-index") else None
        if soup.find_all("div","wp-block-image"):
            for img in soup.find_all("div","wp-block-image"):
                images.append(img.find("img").get("src"))
        item["images"] = images
        abstract = soup.select_one("div.wpb_wrapper > div > div > p").text.strip() if soup.select_one("div.wpb_wrapper > div > div > p") else None
        item["abstract"] = abstract
        body = soup.find(class_="tdb-caption-text").text.strip()+'\n' if soup.find(class_="tdb-caption-text") else ''
        for p in soup.select("div.wpb_wrapper > div > div > p"):
            body += ( p.text.strip() + '\n')
        item["body"] = body

        self.logger.info(item)
        self.logger.info('\n')

        yield item


