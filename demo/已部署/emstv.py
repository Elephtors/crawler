import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#author:甘番雨
#将爬虫类名和name字段改成对应的网站名
class emstv(scrapy.Spider):
    name = 'emstv'
    website_id = 1072 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['http://www.emstv.in/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(emstv, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        soup=BeautifulSoup(response.text,'lxml')

        cat1_list=soup.select('.nav>li>a')

        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            url=url.replace('./','http://www.emstv.in/')
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    def parse_category2(self,response):

        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.select('.col-md-8 h5>a,.read-more')
        for url in url_list:
            news_url=url.get('href')
            news_url=news_url.replace('./','http://www.emstv.in/')
            yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)

    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']
        item['title']=soup.select('#ccr-article>h1>a')[0].text if soup.select('#ccr-article>h1>a') else None

        item['body'] = ''#不能忘记初始化
        item['abstract']=''#abstract不好提取
        if soup.select('#ccr-article p'):
            item['body']=soup.select('#ccr-article p')[-1].text.strip()

    
        item['images']=[]#无images

        pub=soup.find('time').text.strip() if soup.find('time') else None
        if(pub):
            pub=pub.split('/')
            pub_time=pub[2]+'-'+pub[1]+'-'+pub[0]+' 00:00:00'
            item['pub_time']=pub_time


        yield item
  
