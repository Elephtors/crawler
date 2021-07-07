import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time

class krishakjagatSpider(scrapy.Spider):
    name = 'krishakjagat'
    website_id =  1111 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['krishakjagat.org']
    start_urls = ['https://www.krishakjagat.org/',]

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(krishakjagatSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")
        li = soup.select_one("#menu-item-865")
        item['category1'] = li.select_one("a").text
        # print(category1)
        for a in li.select("ul>li>a"):
            url = a.get("href")
            # item['category2'] = a.text.strip()

            yield scrapy.Request(url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据

    def get_next_page(self, response):
            item = response.meta["item"]
            item['category2'] = response.url.split('/')[4]
            soup = bs(response.text, "html.parser")
            div_list = soup.find("div", class_="article-container").find_all("div", class_="featured-image")
            for div in div_list:
                news_url = div.select_one("a").get("href")
                yield scrapy.Request(news_url,meta=response.meta,callback=self.get_news_detail)

            if self.time == None or Util.format_time3(Util.format_time2(soup.find("div",class_="article-container").find_all("time",class_="entry-date published")[-1].text.strip())) >= int(self.time):
                    next_url = soup.find("li",class_="previous").select_one("a").get("href") if soup.find("li",class_="previous").select_one("a")else None
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

        title = soup.find("h1", class_="entry-title").text.strip()
        pub_time = Util.format_time2(soup.find("article").find("time", class_="entry-date published").text)
        image_list = [img.find_all("img")[-1].get("src") if len(img.find_all("img")) != 0 else None for img in
                      soup.find("article").find_all("div", class_="featured-image")] if soup.find("article") else None
        body = ''
        for li in soup.find("div", class_="entry-content clearfix").select("ul>li"):
            body += (li.text + '\n')
        for p in soup.find("div", class_="entry-content clearfix").select("p"):
            body += (p.text + '\n')

        abstract = soup.find("div", class_="entry-content clearfix").select_one("h4").text if soup.find("div",class_="entry-content clearfix").select_one("h4") else body.split("।")[0]
        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item