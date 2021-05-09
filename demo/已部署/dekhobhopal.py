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
from datetime import datetime

#将爬虫类名和name字段改成对应的网站名
class dekhobhopalSpider(scrapy.Spider):
    name = 'dekhobhopal'
    website_id = 1003 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['http://dekhobhopal.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(dekhobhopalSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select('ul#menu-td-demo-header-menu-1 li a')[2:] if soup.select('ul#menu-td-demo-header-menu-1 li a') else None
        for category in categories:
            category_hrefList.append(category.get('href'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(response.text, features="lxml")

        article_hrefs = []
        if soup.select('div.td-big-grid-wrapper div.td-module-thumb a'):
            for href in soup.select('div.td-big-grid-wrapper div.td-module-thumb a'):
                article_hrefs.append(href.get('href'))
        if soup.select('div.td-block-span6 h3 a'):
            for href in soup.select('div.td-block-span6 h3 a'):
                article_hrefs.append(href.get('href'))

        if soup.select('div.td-ss-main-content span.td-post-date'):
            temp_time = soup.select('div.td-ss-main-content span.td-post-date')[-1].text
            adjusted_time = time_adjustment(temp_time)
            if self.time is None or Util.format_time3(adjusted_time) >= int(self.time):
                for detail_url in article_hrefs:
                    yield Request(detail_url, callback=self.parse_detail)
            else:
                self.logger.info("时间截止")
        else:
            check_soup = BeautifulSoup(requests.get(article_hrefs[-1]).content, features="lxml")
            temp_time = check_soup.select_one('header.td-post-title span.td-post-date').text
            adjusted_time = time_adjustment(temp_time)
            if self.time is None or Util.format_time3(adjusted_time) >= int(self.time):
                for detail_url in article_hrefs:
                    yield Request(detail_url, callback=self.parse_detail)
            else:
                self.logger.info("时间截止")



    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['pub_time'] = time_adjustment(soup.select_one('header.td-post-title span.td-post-date').text if soup.select_one('header.td-post-title span.td-post-date').text else None)
        image_list = []
        imgs = soup.select_one('div.td-post-featured-image').select('img') if soup.select_one('div.td-post-featured-image').select('img') else None
        if imgs:
            for img in imgs:
                image_list.append(img.get('src'))
            item['images'] = image_list
        p_list = []
        all_p = soup.find('div', class_='td-post-content tagdiv-type').select('p') if soup.find('div', class_='td-post-content tagdiv-type').select('p') else None
        for paragraph in all_p:
            p_list.append(paragraph.text)
        body = '\n'.join(p_list)
        item['abstract'] = p_list[0]
        item['body'] = body
        item['category1'] = soup.select_one('ul.td-category li').text if soup.select_one('ul.td-category li').text else None
        item['title'] = soup.select_one('h1.entry-title').text if soup.select_one('h1.entry-title').text else None
        yield item



def time_adjustment(input_time):
    time_elements = input_time.split(" ")
    # month = {
    #     'जनवरी': '01',
    #     'फ़रवरी': '02',
    #     'जुलूस': '03',
    #     'अप्रैल': '04',
    #     'मई': '05',
    #     'जून': '06',
    #     'जुलाई': '07',
    #     'अगस्त': '08',
    #     'सितंबर': '09',
    #     'अक्टूबर': '10',
    #     'नवंबर': '11',
    #     'दिसंबर': '12'
    # }
    month = {
        'January': '01',
        'February': '02',
        'March': '03',
        'April': '04',
        'May': '05',
        'June': '06',
        'July': '07',
        'August': '08',
        'September': '09',
        'October': '10',
        'November': '11',
        'December': '12'
    }
    if int(time_elements[0].strip()[:-2]) < 10:
        day = "0" + time_elements[0].strip()[:-2]
    else:
        day = time_elements[0].strip()[:-2]

    return "%s-%s-%s" % (time_elements[2], month[time_elements[1]], day) + " 00:00:00"


