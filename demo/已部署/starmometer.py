# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


#将爬虫类名和name字段改成对应的网站名
class starmometer(scrapy.Spider):
    name = 'starmometer'
    website_id = 1239 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://starmometer.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(starmometer, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        soup=BeautifulSoup(response.text,'lxml')
        cat1_list=soup.select('#menu-main-menu-1 a')
        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)
    
    def parse_category2(self,response):
        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.select('.loop-data>.loop-title>a')
        for url in url_list:
            news_url=url.get('href')
            yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)
        #翻页
        if soup.select('.loop-data>.meta'):
            ddl=soup.select('.loop-data>.meta')[0].text.strip()
            ex='(.*?)//.*?'
            ddl=re.findall(ex,ddl,re.S)#January 10, 2021,得到列表
            ddl=Util.format_time2(ddl[0])#2021-01-10 00:00:00
            ddl=Util.format_time3(ddl)#1610208000
        else:
            ddl=None
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

        item['title']=soup.find('h1',class_='entry-title').text.strip() if soup.find('h1',class_='entry-title') else None
    
        item['body'] = ''#不能忘记初始化
        body_list=soup.find('div',class_='entry clearfix').select('p') if soup.find('div',class_='entry clearfix').select('p')else None
        for body in body_list:
            item['body'] += body.text.strip()
            item['body'] +='\n'
        item['abstract']=soup.find('div',class_='entry clearfix').select('p')[0].text.strip() if soup.find('div',class_='entry clearfix').select('p') else None
   
        item['images']=[]
        image_list=soup.find('div',class_='entry clearfix').select('p>img')if soup.find('div',class_='entry clearfix').select('p>img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images'].append(image)


        pub=soup.find('span',class_='updated').text.strip() if soup.find('span',class_='updated').text.strip() else None
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub

        yield item