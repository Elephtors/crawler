
import re
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response

#将爬虫类名和name字段改成对应的网站名
class apnliveSpider(scrapy.Spider):
    name = 'apnlive'
    website_id = 1140 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['https://hindi.apnlive.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(apnliveSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta["title"] = ''
        soup = BeautifulSoup(response.text)
        category1_list = soup.select("ul#menu-menu-1 > li")
        for category1 in category1_list[1:]:
            if category1.select("ul.sub-menu"):
                meta["category1"] = category1.select_one("div.tdb-menu-item-text").text.strip()
                category2_list = category1.select("ul.sub-menu>li")
                for category2 in category2_list:
                    meta["category2"] = category2.select_one("div.tdb-menu-item-text").text.strip()
                    url = category2.select_one("a").get("href")
                    meta["page_url"] = url + "page/"
                    meta["page"] = 1
                    yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)
            else:
                meta["category1"] = category1.select_one("div.tdb-menu-item-text").text.strip()
                url = category1.select_one("a").get("href")
                meta["page_url"] = url + "page/"
                meta["page"] = 1
                yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)

    def parse_news_list(self, response):
        soup = BeautifulSoup(response.text)
        temp = soup.find_all("div", class_="td_block_inner tdb-block-inner td-fix-index")[-1]
        news_list = temp.find_all("div", class_="td-module-meta-info")
        for n in news_list:
            url = n.select_one("h3>a").get("href")
            response.meta["title"] = n.select_one("h3>a").get("title")
            yield scrapy.Request(url, meta=response.meta, callback=self.parse_news)
        # 时间戳
        page_number = soup.select_one("span.pages").text.strip().split(" ") if soup.select_one("span.pages") else None
        if page_number and response.meta["page"] < int(page_number[-1]):
            last_news_time = news_list[-1].find("time").get("datetime")
            time_list = re.split("T|\+", last_news_time)
            time2 = time_list[0] + " " + time_list[1]
            response.meta["page"] += 1
            next_page = response.meta["page_url"] + str(response.meta["page"]) + '/'
            if self.time == None or Util.format_time3(time2) >= int(self.time):
                yield scrapy.Request(next_page, meta=response.meta, callback=self.parse_news_list)
            else:
                self.logger.info('时间截止')

    def parse_news(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text)
        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        item["title"] = response.meta["title"]
        # 发布时间
        news_time = soup.find("time", class_="entry-date updated td-module-date").get("datetime") if soup.find("time", class_="entry-date updated td-module-date") else None
        time_list = re.split("T|\+", news_time) if news_time else []
        item["pub_time"] = time_list[0] + " " + time_list[1] if time_list else Util.format_time()
        # 图片
        images = []
        temp = soup.select_one("div.td-post-featured-image a") if soup.select_one("div.td-post-featured-image a") else None
        img = temp.get("href") if temp and temp.get("href") else None
        if img:
            images.append(img)
        item["images"] = images
        # 新闻正文
        body = []
        p_list = soup.select("div.td-fix-index>p")
        for p in p_list:
            if p.text:
                body.append(p.text.strip())
        if body == []:
            p_list = soup.select("div.td-ss-main-content p")
            for p in p_list:
                if p.text:
                    body.append(p.text.strip())
        item['body'] = "\n".join(body) if body else None
        item["abstract"] = body[0] if body else None
        yield item