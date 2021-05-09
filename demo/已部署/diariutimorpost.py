
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re

#将爬虫类名和name字段改成对应的网站名
class diariutimorpostSpider(scrapy.Spider):
    name = 'diariutimorpost'
    website_id = 690 # 网站的id(必填)
    language_id = 2122  # 所用语言的id
    start_urls = ['http://diariutimorpost.com/pt/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(diariutimorpostSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select("div#headerNav ul#menu-main-menu li a") if soup.select("div#headerNav ul#menu-main-menu li a") else None
        del categories[0]
        for category in categories:
            category_hrefList.append(category.get('href'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")

        article_hrefs = []
        articles = soup.select('div.title h3.h4 a') if soup.select('div.title h3.h4 a') else None
        if articles:
            meta = {
                "category1": re.findall(r'Category: (\S+)',soup.select_one('div.post--items-title h2.h4').text)[0]
            }
            temp_time = soup.select('div.post--info ul li')[-1].text if soup.select('div.post--info ul li')[-1].text else None
            adjusted_time = Util.format_time2(temp_time)
            if self.time is None or Util.format_time3(adjusted_time) >= int(self.time):
                for href in articles:
                    article_hrefs.append(href.get('href'))
                for detail_url in article_hrefs:
                    yield Request(detail_url, callback=self.parse_detail, meta=meta)
            else:
                self.logger.info("时间截止")




    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['category1'] = response.meta["category1"]
        item['title'] = soup.select_one('div.title h2.titlePostDetail').text if soup.select_one('div.title h2.titlePostDetail').text else None
        item['pub_time'] = Util.format_time2(soup.select('.post--info li span')[0].text)
        p_list = []
        if soup.select('div.post--content h4,div.post--content p'):
            all_p = soup.select('div.post--content h4,div.post--content p')
            for paragraph in all_p:
                p_list.append(paragraph.text)
            body = '\n'.join(p_list)
            item['abstract'] = p_list[0]
            item['body'] = body
        image_list = []
        imgs = soup.select('div.post--img a img') if soup.select('div.post--img a img') else None
        if imgs:
            for img in imgs:
                image_list.append(img.get('src'))
            item['images'] = image_list

        yield item

