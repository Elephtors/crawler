
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


#将爬虫类名和name字段改成对应的网站名
class pinoyparazzi(scrapy.Spider):
    name = 'pinoyparazzi'
    website_id = 1241 # 网站的id(必填)
    language_id = 1880 # 所用语言的id
    start_urls = ['https://www.pinoyparazzi.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(pinoyparazzi, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        soup=BeautifulSoup(response.text,'lxml')
        cat1_list=soup.select('#menu-header-1>li>a')
        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    
    def parse_category2(self,response):
        soup=BeautifulSoup(response.text,'lxml')
        cat2_list=soup.find_all('a',class_='td-pulldown-category-filter-link')
        for cat2 in cat2_list:
            url=cat2['href']
            response.meta['category2']=cat2.text
            yield scrapy.Request(url,meta=response.meta,callback=self.parse_newslist)

    def parse_newslist(self,response):
        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.select('.td-ss-main-content .entry-title>a') if soup.select('.td-ss-main-content .entry-title>a') else None
        if(url_list):
            for url in url_list:
                news_url=url.get('href')
                yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)
                

        ddl=soup.select('.td-ss-main-content time')[0].text.strip() if soup.select('.td-ss-main-content time') else None#January 10, 2021
        if(ddl):
            ddl=Util.format_time2(ddl)#2021-01-10 00:00:00
            ddl=Util.format_time3(ddl)#1610208000

        #翻页
        if soup.select('.page-nav>a'):
            next_url=soup.select('.page-nav>a')[-1].get('href')
            if(self.time==None or ddl>=int(self.time)):
                yield scrapy.Request(next_url,meta=response.meta,callback=self.parse_newslist)
            else:
                self.logger.info('时间截止')

    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']
        item['title']=soup.find('h1',class_='entry-title').text.strip() if soup.find('h1',class_='entry-title') else None
 
        item['body'] = ''#不能忘记初始化
        body_list=soup.find('div',class_='td-post-content tagdiv-type').select('p') if soup.find('div',class_='td-post-content tagdiv-type').select('p') else None

        if(body_list):
            for body in body_list:
                item['body'] += body.text.strip()
                item['body'] +='\n'

        item['abstract']=soup.find('div',class_='td-post-content tagdiv-type').select('p')[0].text.strip() if soup.find('div',class_='td-post-content tagdiv-type').select('p') else None
        
        item['images']=[]         
        image_list=soup.select('.wp-caption>img')if soup.select('.wp-caption>img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images'].append(image)
                
        pub=soup.find('time',class_='entry-date updated td-module-date').text.strip() if soup.find('time',class_='entry-date updated td-module-date') else None
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub

        
        yield item
            

