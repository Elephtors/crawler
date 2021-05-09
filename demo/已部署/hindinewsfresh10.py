import socket
# 此文件包含的头文件不要修改
import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#将爬虫类名和name字段改成对应的网站名
class aajkaSpider(scrapy.Spider):
    name = 'hindinewsfresh10'
    website_id = 967  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://hindinewsfresh10.blogspot.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(aajkaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select('ul#nav2 li a') if soup.select('ul#nav2 li a') else None
        for category in categories:
            category_hrefList.append(category.get('href').replace(' ', '%20'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        articles = soup.find_all('h2',class_="post-title entry-title")
        article_hrefs = []
        for article in articles:
            article_href = article.select_one('a').get('href')
            article_hrefs.append(article_href)
        meta = {}
        abstract = soup.select_one('div.post-snippet p').text if soup.select_one('div.post-snippet p').text else None
        meta['abstract'] = abstract
        #最新news
        for detail_url in article_hrefs:
            yield Request(detail_url, callback=self.parse_detail, meta=meta)
        #以前news
        previous_href = soup.select_one('a.blog-pager-older-link').get('href')
        yield Request(previous_href, callback=self.parse_previous, meta=meta)



    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text)
        temp_time = soup.select_one('abbr.published').text if soup.select_one('abbr.published').text else None
        adjusted_time = time_adjustment(temp_time)
        item['pub_time'] = adjusted_time
        image_list = []
        imgs = soup.select('.post-article img')
        for img in imgs:
            if img.get('src'):
                image_list.append(img.get('src'))
        item['images'] = image_list
        item['abstract'] = response.meta['abstract']
        item['body'] = soup.find('div', class_="post-body entry-content").text if soup.find('div', class_="post-body entry-content").text else None
        news_categories = soup.find('div', class_="label-head Label").select('a') if soup.find('div', class_="label-head Label").select('a') else None
        item['category1'] = news_categories[0].text if news_categories[0].text else None
        if len(news_categories) >= 2:
            item['category2'] = news_categories[1].text
        item['title'] = soup.find('h1', class_="post-title entry-title").text if soup.find('h1', class_="post-title entry-title").text else None
        yield item

    def parse_previous(self, response):
        socket.setdefaulttimeout(30)
        if BeautifulSoup(response.text, features="lxml").select('div.post-outer'):
            soup = BeautifulSoup(response.text, features="lxml")
            articles = soup.find_all('h2', class_="post-title entry-title")

            article_hrefs = []
            for article in articles:
                article_href = article.select_one('a').get('href')
                article_hrefs.append(article_href)

            for detail_url in article_hrefs:
                yield Request(detail_url, callback=self.parse_detail, meta=response.meta)


            adjusted_time = time_adjustment(soup.select('abbr.published')[-1].text if soup.select('abbr.published')[-1].text else None)
            if self.time is None or Util.format_time3(adjusted_time) >= int(self.time):
                next_page = soup.select_one('a.blog-pager-older-link').get('href') if soup.select_one('a.blog-pager-older-link').get('href') else None
                check_soup = BeautifulSoup(requests.get(next_page).content, features="lxml")
                if check_soup.find('div', class_="widget Blog").find('div', class_="blog-posts hfeed").select('div.post-outer'):
                    yield Request(next_page, callback=self.parse_previous, meta=response.meta)
                else:
                    self.logger.info("最后一页了")
            else:
                self.logger.info("时间截止")
        else:
            self.logger.info("页面为空")

def time_adjustment(input_time):
    get_year = input_time.split(", ")
    month_day = get_year[0].split(" ")
    if month_day[0] == "जनवरी":
        month = "01"
    elif month_day[0] == "फ़रवरी":
        month = "02"
    elif month_day[0] == "मार्च":
        month = "03"
    elif month_day[0] == "अप्रैल":
        month = "04"
    elif month_day[0] == "मई":
        month = "05"
    elif month_day[0] == "जून":
        month = "06"
    elif month_day[0] == "जुलाई":
        month = "07"
    elif month_day[0] == "अगस्त":
        month = "08"
    elif month_day[0] == "सितंबर":
        month = "09"
    elif month_day[0] == "अक्टूबर":
        month = "10"
    elif month_day[0] == "नवंबर":
        month = "11"
    elif month_day[0] == "दिसंबर":
        month = "12"
    else:
        month = "None"

    day = month_day[1]

    return "%s-%s-%s" % (get_year[1], month, day) + " 00:00:00"
