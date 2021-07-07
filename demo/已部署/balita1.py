import datetime
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time

class Balita1Spider(scrapy.Spider):
    name = 'balita1'
    allowed_domains = ['balita.ph']
    start_urls = [#'https://balita.ph/',
                  'https://balita.ph/category/news/',
                  'https://balita.ph/category/world/',
                  'https://balita.ph/category/economy/',
                  'https://balita.ph/category/entertainment/',
                  'https://balita.ph/category/sports/',
                  'https://balita.ph/category/lifestyle/',
                  'https://balita.ph/category/technology/',
                  'https://balita.ph/category/opinion/']
    website_id = 498
    language_id = 1866
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(Balita1Spider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        soup = bs(response.text,"html.parser")
        category2_url =[li.find("a").get("href") for li in soup.find_all("li","td-pulldown-filter-item")]
        # print(category2_url)
        for url in category2_url:
            yield scrapy.Request(url,callback=self.parse_page)

    def parse_page(self,response):
        meta={}
        soup = bs(response.text,"html.parser")

        l_list = soup.find_all("h3","entry-title td-module-title") if soup.find_all("h3","entry-title td-module-title") else None
        if l_list:
            for l in l_list:
                news_url = l.find("a").get("href")
                category1 = soup.select_one("#td-outer-wrap > div > div > div > div > h1").text.strip()
                meta["category1"] = category1
                category2 = soup.find("div", "td-pulldown-filter-display-option").select_one("div").text.strip()
                meta["category2"] = category2
                yield scrapy.Request(news_url,callback=self.parse_news,meta=meta)

        pub_time = soup.find_all(class_="entry-date updated td-module-date")[-1].text.strip()
        if self.time == None or Util.format_time3(Util.format_time2(pub_time)) >= int(self.time):
            url = soup.find(class_="page-nav td-pb-padding-side").select("a")[-1].get("href") if soup.find(class_="page-nav td-pb-padding-side") else None
            if url:
                if soup.find(class_="current").text.strip() == soup.find(class_="last"):
                    pass
                else:
                    self.logger.info(url)
                    yield scrapy.Request(url,callback=self.parse_page)
        else:
            self.logger.info('时间截止')

    def parse_news(self,response):
        soup = bs(response.text,"html.parser")
        item = DemoItem()

        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        pub_time = soup.find("time","entry-date updated td-module-date").text.strip() if soup.find("time","entry-date updated td-module-date") else "0000-00-00 00:00:00"
        item["pub_time"] = Util.format_time2(pub_time)
        title = soup.find("h1","entry-title").text.strip() if soup.find("h1","entry-title") else None
        item["title"] = title
        div = soup.find("div","td-post-content tagdiv-type")
        images = [ img.get("src") for img in div.find_all("img")] if div.find_all("img") else None
        abstract = div.find("p").text.strip()
        body = [p.text.strip() for p in div.find_all("p")] if div.find_all("p") else None
        if abstract:
            body = "\n".join(body)
        else:
            abstract = div.find("h4").text.strip()
            body = [h.text.strip() for h in div.find_all("h4")] if div.find_all("h4") else None
            body = "\n".join(body)
        item["images"] = images
        item["abstract"] = abstract
        item["body"] = body
        yield item

