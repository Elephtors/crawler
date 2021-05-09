
# 此文件包含的头文件不要修改
import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import socket

#将爬虫类名和name字段改成对应的网站名
class ambalaSpider(scrapy.Spider):
    name = 'ambala'
    website_id = 965  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['http://ambalavaani.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(ambalaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):

        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        category_nameList = []
        categories = soup.select('nav ul li') if soup.select('nav ul li') else None
        for category in categories:
            category_hrefList.append(category.find("a").get("href"))
            category_nameList.append(category.text.replace('\n', ''))
        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(response.text, features="lxml")

        articles = soup.select('div.article-three-posts article')
        article_hrefs = []
        for article in articles:
            article_href = article.select_one('a')
            article_hrefs.append(article_href.get('href'))

        for detail_url in article_hrefs:
            yield Request(detail_url, callback=self.parse_detail)

        check_soup = BeautifulSoup(requests.get(article_hrefs[-1]).content)     #不加content会出错，原因是因为这里的wb_data是requests对象，无法用BeautifulSoup解析
        temp_time = check_soup.find('span', class_="thetime date updated").text if check_soup.find('span', class_="thetime date updated").text else None
        adjusted_time = time_adjustment(temp_time)
        if self.time == None or Util.format_time3(adjusted_time) >= int(self.time):
            try:
                if soup.select_one('li.nav-previous a').get('href'):
                    yield Request(soup.select_one('li.nav-previous a').get('href'), callback=self.parse_category)
            except:
                print("没得再前了")
        else:
            self.logger.info("时间截止")

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        temp_time = soup.find('span', class_="thetime date updated").text if soup.find('span', class_="thetime date updated").text else None
        adjusted_time = time_adjustment(temp_time)
        if self.time == None or Util.format_time3(adjusted_time) >= int(self.time):
            all_text = soup.select_one('div.thecontent').text.replace('\nAdvertisements\n', '') if soup.select_one('div.thecontent').text.replace('\nAdvertisements\n', '') else None
            item['body'] = all_text

            item['pub_time'] = adjusted_time
            item['abstract'] = soup.select_one('div.thecontent p').text if soup.select_one('div.thecontent p').text else None
            item['category1'] = soup.select_one('span.thecategory').text if soup.select_one('span.thecategory').text else None
            item['title'] = soup.select_one('header h1').text if soup.select_one('header h1').text else None
            yield item
        else:
            self.logger.info("时间截止")

def time_adjustment(input_time):
    get_year = input_time.split(", ")
    month_day = get_year[0].split(" ")
    if month_day[0] == "January":
        month = "01"
    elif month_day[0] == "February":
        month = "02"
    elif month_day[0] == "March":
        month = "03"
    elif month_day[0] == "April":
        month = "04"
    elif month_day[0] == "May":
        month = "05"
    elif month_day[0] == "June":
        month = "06"
    elif month_day[0] == "July":
        month = "07"
    elif month_day[0] == "August":
        month = "08"
    elif month_day[0] == "September":
        month = "09"
    elif month_day[0] == "October":
        month = "10"
    elif month_day[0] == "November":
        month = "11"
    elif month_day[0] == "December":
        month = "12"
    else:
        month = "None"

    if int(month_day[1]) < 10:
        day = "0" + month_day[1]
    else:
        day = month_day[1]

    return "%s-%s-%s" % (get_year[1], month, day) + " 00:00:00"