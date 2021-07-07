import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time


class agnibanSpider(scrapy.Spider):
    name = 'agniban'
    website_id =  1108 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['news.agniban.com']
    start_urls = ['https://news.agniban.com/',]

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(agnibanSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")
        for li in soup.find("ul", class_="menu").select("li")[:-1]:
            if li.find("ul") == None:  # 没有2级目录
                url = li.select_one("a").get("href")
                # name = li.select_one("a").text
                yield scrapy.Request(url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据

    def get_next_page(self, response):

            item = response.meta["item"]
            soup = bs(response.text, "html.parser")
            div = soup.find("div", class_="twp-row")
            for article in div.find_all("a", class_="post-thumbnail"):
                news_url = article.get("href")
                item['category1'] = soup.find_all("li",class_="trail-item")[1].text
                item['category2'] = soup.find_all("li", class_="trail-item")[2].text if len(soup.find_all("li", class_="trail-item")) > 3 or (soup.find_all("li", class_="trail-item")[-1].text.split(" ")[0] != "Page" and len(soup.find_all("li", class_="trail-item")) == 3) else None

                yield scrapy.Request(news_url,meta=response.meta,callback=self.get_news_detail)

            if self.time == None or Util.format_time3(Util.format_time2(div.find_all("span",class_="item-metadata posts-date")[-1].text.strip())) >= int(self.time):
                    next_url = soup.find("a",class_="next page-numbers").get("href") if  soup.find("a",class_="next page-numbers")else None
                    if next_url:
                        yield scrapy.Request(next_url, meta=response.meta, callback=self.get_next_page)
            else:
                self.logger.info('时间截止')

    def get_news_detail(self,response):
        '''
        :param response: x新闻正文response
        :return: 新闻页面详情信息
        '''
        item = response.meta["item"]

        soup = bs(response.text, "html.parser")

        article = soup.select_one("article")
        title = article.find("h1", class_="entry-title twp-secondary-title").text.strip()
        pub_time = article.find("span", class_="item-metadata posts-date").text
        image_list = [img.get("src") for img in article.select("p>img")]
        body = ''
        for p in article.select("p"):
            body += (p.text + '\n')
        abstract = body.split("।", 1)[0]
        item["title"] = title
        item["pub_time"] = Util.format_time2(pub_time)
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item