
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


#将爬虫类名和name字段改成对应的网站名
class technobaboy(scrapy.Spider):
    name = 'technobaboy'
    website_id = 1246 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.technobaboy.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(technobaboy, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        soup=BeautifulSoup(response.text,'lxml')
        cat1_list=soup.find('ul',class_='menu').select('li>a')
        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    def parse_category2(self,response):
        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.select('.col-12 .content h2 a') if soup.select('.col-12 .content h2 a') else None
        if(url_list):
            for url in url_list:
                news_url=url.get('href')
                yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)
        if soup.find('span',class_='page-numbers label-next'):
            next_url=soup.find('span',class_='page-numbers label-next').find('a').get('href')
            if self.time==None or Util.format_time3(Util.format_time2(soup.select('.posts-wrap time')[-1].text)) >= int(self.time):
                yield scrapy.Request(next_url,meta=response.meta,callback=self.parse_category2)
            else:
                self.logger.info('时间截止')

    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']
        
        item['title']=soup.find('h1',class_='post-title').text.strip() if soup.find('h1',class_='post-title') else None
       
        item['body'] = ''#不能忘记初始化
        body_list=soup.find('div',class_='post-content description cf entry-content content-spacious').select('p') if soup.find('div',class_='post-content description cf entry-content content-spacious').select('p') else None
        if(body_list):
            for body in body_list:
                item['body'] += body.text.strip()
                item['body'] +='\n'
        

        item['abstract']=soup.find('div',class_='post-content description cf entry-content content-spacious').select('p')[0].text.strip() if soup.find('div',class_='post-content description cf entry-content content-spacious').select('p') else None
        

        item['images']=[]
        

        image_list_0=soup.select('.featured>a')if soup.select('.featured>a') else None
        if(image_list_0):
            for image_0 in image_list_0:
                image_0=image_0.get('href')
                item['images'].append(image_0)
                


        image_list=soup.find('div',class_='post-content description cf entry-content content-spacious').select('img')if soup.find('div',class_='post-content description cf entry-content content-spacious').select('img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images'].append(image)
                
        
        pub=soup.find('time',class_='post-date').text.strip() if soup.find('time',class_='post-date') else None
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub
            print(item['pub_time'])

        yield item