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
#列表处没时间只有进去文章才有时间
class bhadas4media(scrapy.Spider):
    name = 'bhadas4media'
    website_id = 1061 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['http://bhadas4media.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(bhadas4media, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        meta['next_url']=''
        soup=BeautifulSoup(response.text)
        cat1_list=soup.select('.collapse a.menu-item')

        for cat1 in cat1_list:
            url=cat1['href'] if (cat1.get('href')) else None
            meta['category1']=cat1.text
            if url != None:
                yield scrapy.Request(url,meta=meta,callback=self.parse_category2)
            
    def parse_category2(self,response):
        soup=BeautifulSoup(response.text)

        #爬取可翻页列表中的新闻
        url_list=soup.select('.row .col-md-9>a')
        for url in url_list[:-1]:#到倒数第二篇
            news_url=url.get('href')
            yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)
        #爬取latest100新闻
        latest_list=soup.select('.widget_recent_entries li>a')
        for latest_url in latest_list:
            latest_url=latest_url.get('href')
            yield scrapy.Request(latest_url,meta=response.meta,callback=self.parse_details)
        # 这里在可翻页列表中挑选最后一篇文章并传给parse_page，并通过meta把下一页的url也传过去用于翻页，dont_filter防止文章被查重
        response.meta['next_url']=soup.select('.wp-pagenavi a.nextpostslink')[0].attrs['href'] if soup.select('a.nextpostslink') else None
        if response.meta['next_url'] != None:
            response.meta['dont_filter'] = True
            yield Request(soup.select('.row .col-md-9>a')[-1].attrs['href'],callback=self.parse_page,meta=response.meta,dont_filter=True)
        else:
            self.logger.info('最后一页')

    def parse_page(self, response): # 用于判断是否截止
        soup = BeautifulSoup(response.text)
        response.meta['dont_filter'] = False
        time=soup.find('time',class_='entry-date published').text.strip() if soup.find('time',class_='entry-date published') else None#March 28, 2021
        time=Util.format_time2(time)
        time=Util.format_time3(time)#转换为时间戳
        if self.time == None or time >= int(self.time):
            #这里使用的在上一层爬取了下一页的url后传过来
            yield Request(response.meta['next_url'],meta=response.meta,callback=self.parse_category2)
        else:
            self.logger.info('截止')
        #判断完就把文章传给parse_details
        yield Request(response.url,meta=response.meta,callback=self.parse_details)

    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']

        item['title']=soup.find('h1',class_='entry-title').text.strip() if soup.find('h1',class_='entry-title') else None

        item['body'] = ''#不能忘记初始化
        if soup.select('.entry-content p'):
            body_list=soup.select('.entry-content p')
            for body in body_list:
                item['body'] += body.text.strip()
                item['body'] +='\n'
            item['abstract']=body_list[0].text.strip() 
        
        item['images']=[]
        image_list=soup.select('.entry-content .wp-block-image>figure>img')if soup.select('.entry-content .wp-block-image>figure>img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images'].append(image)


        pub=soup.find('time',class_='entry-date published').text.strip() if soup.find('time',class_='entry-date published') else None
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub

        
        yield item




