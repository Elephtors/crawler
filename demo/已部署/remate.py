import scrapy
import time
from bs4 import BeautifulSoup as bs
import datetime
import re
from demo.util import Util
from demo.items import DemoItem


class RemateSpider(scrapy.Spider):
    name = 'remate'
    allowed_domains = ['www.remate.ph']
    start_urls = ['https://www.remate.ph/news/',
                  'https://www.remate.ph/sports/',
                  'https://www.remate.ph/lifestyle/',
                  'https://www.remate.ph/tech-trend/',
                  'https://www.remate.ph/entertainment/',
                  'https://www.remate.ph/opinion/']

    website_id = 533
    language_id = 2117
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(RemateSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        soup = bs(response.text)

        a_list = ["https://www.remate.ph" + a.find("a").get("href") for a in soup.find_all("div","vc_btn3-container vc_btn3-center")]if soup.find_all("div","vc_btn3-container vc_btn3-center") else None
        if a_list:
            for url in a_list:
                yield scrapy.Request(url,callback=self.parse_page)
        else:
                yield scrapy.Request("https://www.remate.ph"+soup.select('.wpb_wrapper.vc_column-inner a')[-1].attrs['href'], callback=self.parse_page)

    def parse_page(self,response):
        meta = {}
        soup = bs(response.text)
        category1 = soup.select(".breadcrumb > li")[1].text if soup.select(".breadcrumb > li") else None
        if category1 == 'SPORTS' or category1 == 'OPINION' or category1 == 'TECH TREND':
            category2 = None
        else:
            category2 = soup.select(".breadcrumb > li")[2].text.strip() if soup.select(".breadcrumb > li")[2] else None
        meta["category1"] = category1
        meta["category2"] = category2
        for i in soup.find_all(class_="entry-title"):
            news_url = i.find("a").get("href")
            yield scrapy.Request(news_url,callback=self.parse_news,meta=meta)
        if self.time == None or Util.format_time3(Util.format_time2(soup.select('article .meta-date')[-1].text)) >= int(self.time):
            url = soup.find(class_="next page-numbers").get("href") if soup.find(class_="next page-numbers") else None
            if url:
                yield scrapy.Request(url,callback=self.parse_page)
        else:
            self.logger.info('时间截止')


    def parse_news(self,response):
        soup = bs(response.text)
        item = DemoItem()

        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        item["pub_time"] = Util.format_time2(soup.select('article .meta-date')[0].text)

        title = soup.select_one("#content > article > h1").text.strip() if soup.select_one("#content > article > h1") else None
        item["title"] = title
        images = [img.get("src") for img in soup.select_one("#content > article").find_all("img")] if soup.select_one("#content > article").find_all("img") else None
        item["images"] = images
        abstract = soup.select_one("#content > article").find("h4").text.strip() if soup.select_one("#content > article").find("h4") else None
        body = [h.text.strip() for h in soup.select_one("#content > article").find_all("h4")] if soup.select_one("#content > article").find_all("h4") else None
        if abstract:
            body = "\n".join(body)
        else:
            abstract = soup.select_one("#content > article").find("p").text.strip() if soup.select_one("#content > article").find("p") else None
            body = [p.text.strip() for p in soup.select_one("#content > article").find_all("p")] if soup.select_one("#content > article").find_all("p") else None
            body = "\n".join(body)
        item["abstract"] = abstract
        item["body"] = body
        yield item

