import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import socket

#将爬虫类名和name字段改成对应的网站名
class mattscradle(scrapy.Spider):
    name = 'mattscradle'
    website_id = 1232 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://mattscradle.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(mattscradle, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        soup=BeautifulSoup(response.text,'lxml')
        cat1_list=soup.select('#menu-home li>a')
        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    def parse_category2(self,response):
        socket.setdefaulttimeout(30)
        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.find_all('h2',class_='headline') if soup.find_all('h2',class_='headline') else None
        if(url_list):
            for url in url_list:
                news_url=url.find('a').get('href')
                yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)
                

        ddl_url=soup.select('.headline>a')[0].get('href') if soup.select('.headline>a') else None
        if(ddl_url):
            ddl_soup=BeautifulSoup(requests.get(ddl_url).text,'lxml')
            ddl=ddl_soup.find('span',class_='post_date date_modified').text.strip()#January 10, 2021
            ddl=Util.format_time2(ddl)#2021-01-10 00:00:00
            ddl=Util.format_time3(ddl)#1610208000

        #翻页
        if soup.find('span',class_='previous_posts'):
            next_url=soup.find('span',class_='previous_posts').find('a').get('href')
            if(self.time==None or ddl>=int(self.time)):
                yield scrapy.Request(next_url,meta=response.meta,callback=self.parse_category2)
            else:
                self.logger.info('时间截止')


    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']

        item['title']=soup.find('h1',class_='headline').text.strip() if soup.find('h1',class_='headline') else None

        item['body'] = ''#不能忘记初始化
        item['body']=soup.find('div',class_='post_content').text.strip() if soup.find('div',class_='post_content') else None


        item['abstract']=soup.select('.post_content>p')[0].text.strip() if soup.select('.post_content>p') else None

        item['images']=[]        
        image_list=soup.select('.post_content img')if soup.select('.post_content img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images'].append(image)
                
        pub=soup.find('span',class_='post_date date_modified').text.strip() if soup.find('span',class_='post_date date_modified') else None
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub

        yield item