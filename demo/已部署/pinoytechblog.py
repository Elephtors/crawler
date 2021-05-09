
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


#将爬虫类名和name字段改成对应的网站名
class pinoytechblog(scrapy.Spider):
    name = 'pinoytechblog'
    website_id = 1245 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.pinoytechblog.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(pinoytechblog, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        soup=BeautifulSoup(response.text,'lxml')
        cat1_list=soup.select('#menu-main-1>li>a')
        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    def parse_category2(self,response):
        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.find_all('h2',class_='entry-title grid-title') 
        for url in url_list:
            news_url=url.find('a').get('href')
            yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)

        #截止时间  
        ddl=soup.find('time',class_='entry-date published').text.strip()#January 10, 2021
        ddl=Util.format_time2(ddl)#2021-01-10 00:00:00
        ddl=Util.format_time3(ddl)#1610208000

        #翻页
        if soup.find('a',class_='next page-numbers'):
            next_url=soup.find('a',class_='next page-numbers').get('href')
            if(self.time==None or ddl>=int(self.time)):
                yield scrapy.Request(next_url,meta=response.meta,callback=self.parse_category2)
            else:
                self.logger.info('时间截止')

    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']
        item['title']=soup.find('h1',class_='post-title single-post-title entry-title').text.strip() if soup.find('h1',class_='post-title single-post-title entry-title') else None
       
        item['body'] = ''#不能忘记初始化
        body_list=soup.find('div',class_='inner-post-entry entry-content').select('p') if soup.find('div',class_='inner-post-entry entry-content').select('p') else None

        if(body_list):
            for body in body_list:
                item['body'] += body.text.strip()
                item['body'] +='\n'

      

        item['abstract']=soup.find('div',class_='inner-post-entry entry-content').select('p')[0].text.strip() if soup.find('div',class_='inner-post-entry entry-content').select('p') else None
       

        item['images']=[]
    
                
        image_list=soup.find('div',class_='inner-post-entry entry-content').select('img')if soup.find('div',class_='inner-post-entry entry-content').select('img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images'].append(image)
                
        pub=soup.find('time',class_='entry-date published').text.strip() if soup.find('time',class_='entry-date published') else None
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub

        yield item
