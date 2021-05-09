import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time
class pravakta(scrapy.Spider):
    name = 'pravakta'
    website_id =  1076 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['pravakta.com']
    start_urls = ['http://www.pravakta.com/']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(pravakta, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item =DemoItem()
        soup = bs(response.text, "html.parser")

        sub_ul = soup.find_all("ul", class_="sub-menu")
        url_list = []

        for ul in sub_ul:
            sub_a = ul.select("li>a")
            for a in sub_a:
                if ul == sub_ul[-1]:  # "关于我们"一栏不要
                    pass
                else:
                    url = a.get("href")
                    item['category2'] = a.text.split(",")[0]
                    url_list.append(url)#category2要是不赋值自动为0？
                    yield scrapy.Request(url, callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据
        about_us = [a.get("href") for a in soup.find_all("ul", class_="sub-menu")[-1].select("li>a")]
        # 一级目录链接
        ul = soup.find("ul", class_="menu")
        for a in ul.select("li>a")[1:-1]:  # 第一个是home_url,最后一个是视频
            if a.get("href") and a.get("href") not in url_list and a.get("href") != '#' and a.get("href") not in about_us:
                url_list.append(a.get("href"))
                item['category1'] = a.text.strip()
                # item["category2"] =
                if a.get("href")=="https://www.pravakta.com/news/":
                    yield scrapy.Request(a.get("href"), callback=self.get_news_category,meta={"item": item})  # 层与层之间通过meta参数传递数据
                else:
                    yield scrapy.Request(a.get("href"), callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据
    def get_news_category(self,response):
        item = response.meta["item"]
        soup = bs(response.text, "html.parser")
        a_list = soup.find("ul", class_="menu").select("li>a")
        for a in a_list[2:-1]:
            url = a.get("href")
            item['category2'] = a.text.strip()
            yield scrapy.Request(url, callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据
    def get_next_page(self, response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]
            div_list = soup.find_all("div", class_="data-bg-hover data-bg data-bg-categorised")
            for div in div_list:
                article_url = div.select_one("a").get("href")
                # print(article_url)
            # last_time = soup.find_all("span",class_="item-metadata posts-date")[11].text.strip()
                yield scrapy.Request(article_url, callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据

            if self.time == None or Util.format_time3(Util.format_time2(soup.find_all("article")[-1].find("span", class_="item-metadata posts-date").text.strip())) >= int(self.time):
                url = soup.find("a",class_="next page-numbers").get("href") if soup.find("a",class_="next page-numbers") else None
                if url:
                    yield scrapy.Request(url, meta=response.meta, callback=self.get_next_page)
            else:
                self.logger.info('时间截止')

    def get_news_detail(self,response):
        '''
        :param response: x新闻正文response
        :return: 新闻页面详情信息
        '''
        item = response.meta["item"]

        soup = bs(response.text, "html.parser")
        title = soup.find("h1", class_="entry-title").text.strip() if soup.find("h1", class_="entry-title") else None
        pub_time = Util.format_time2(soup.find("span", class_="item-metadata posts-date").text.strip())
        image_list = [soup.find("div", class_="entry-content").find("figure",class_="wp-block-image size-large").select_one("img").get("data-src")] if soup.find("div", class_="entry-content").find("figure",class_="wp-block-image size-large") else []
        body = ''
        for p in soup.find("div", class_="entry-content").select("p"):
            body += (p.text.strip() + '\n')
        if soup.find("pre", class_="wp-block-code"):
            # for code in soup.find("pre", class_="wp-block-code"):
                body += soup.find("pre", class_="wp-block-code").text
        abstract = body.split('।')[0]  # 摘要是文章的第一句话
        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item
