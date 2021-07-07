
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#将爬虫类名和name字段改成对应的网站名
class loktejSpider(scrapy.Spider):
    name = 'loktej'
    website_id = 970 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['http://loktej.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(loktejSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select('ul#menu-below-header-menu li') if soup.select('ul#menu-below-header-menu li') else None
        for category in categories:
            category_hrefList.append(category.select_one('a').get('href'))
            # category_nameList.append(category.text.replace('\n', ''))
        category_hrefList.pop()
        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")

        articles = soup.select('h2.entry-title a')
        article_hrefs = []
        for article in articles:
            article_href = article.get('href')
            article_hrefs.append(article_href)
        for detail_url in article_hrefs:
            yield Request(detail_url, callback=self.parse_detail)

        #时间截止
        if self.time == None or Util.format_time3(time_adjustment(soup.select('span.auth-posted-on time')[-1].text)) >= int(self.time):
            #翻页
            if soup.select_one('div.left-right-links a span.right'):
                page_a = soup.select('div.left-right-links a')
                for a in page_a:
                    if a.text == "Next »":
                        yield Request(a.get('href'), callback=self.parse_category)
        else:
            self.logger.info("时间截止")


    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['pub_time'] = time_adjustment(soup.select_one('div.post-time').text) if soup.select_one('div.post-time').text else None
        image_list = []
        imgs = soup.find('article', class_="post category-single-ebook type-post status-publish format-standard category-news entry").select('img') if soup.find('article', class_="post category-single-ebook type-post status-publish format-standard category-news entry").select('img') else None
        if imgs:
            for img in imgs:
                image_list.append(img.get('src'))
            item['images'] = image_list
        #正文在p里
        if soup.select('div.txt p'):
            all_p = soup.select('div.txt p')
            p_list = []
            for paragraph in all_p:
                p_list.append(paragraph.text)
            body = '\n'.join(p_list)
        #正文在div里
        elif soup.select('div.txt div'):
            all_p = soup.select('div.txt div')
            p_list = []
            for paragraph in all_p:
                p_list.append(paragraph.text)
            body = '\n'.join(p_list)
        item['abstract'] = p_list[0]
        item['body'] = body
        item['category1'] = soup.select_one('li.sinlge-cat-links a').text if soup.select_one('li.sinlge-cat-links a').text else None

        item['title'] = soup.select_one('h3').text if soup.select_one('h3').text else None
        yield item



def time_adjustment(input_time):
    time_elements = input_time.split(' ')
    now_point = time.time()

    if time_elements[1] == "second" or time_elements[1] == "seconds":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_point - float(time_elements[0]) * 1))
    elif time_elements[1] == "min" or time_elements[1] == "mins":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_point - float(time_elements[0]) * 60))
    elif time_elements[1] == "hour" or time_elements[1] == "hours":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_point - float(time_elements[0]) * 3600))
    elif time_elements[1] == "day" or time_elements[1] == "days":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_point - float(time_elements[0]) * 86400))
    elif time_elements[1] == "week" or time_elements[1] == "weeks":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_point - float(time_elements[0]) * 604800))
    elif time_elements[1] == "month" or time_elements[1] == "months":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_point - float(time_elements[0]) * 2419200))
    elif time_elements[1] == "year" or time_elements[1] == "years":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_point - float(time_elements[0]) * 31536000))

