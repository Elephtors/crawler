
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#要加headers！！！！
#将爬虫类名和name字段改成对应的网站名
class coolbuster(scrapy.Spider):
    name = 'coolbuster'
    website_id = 1238 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.coolbuster.net/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(coolbuster, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        meta['abstract']=''
        soup=BeautifulSoup(response.text,'lxml')
        cat1_list=soup.select('#nav-ceebee>ul>li>a')
        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    def parse_category2(self,response):
        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.find_all('div',class_='post hentry') if soup.find_all('div',class_='post hentry') else None
        if(url_list):
            for url in url_list:
                news_url=url.find('h2',class_='post-title entry-title').find('a').get('href') if url.find('h2',class_='post-title entry-title') else None
                response.meta['abstract']=url.find('div',class_='post-snippet').text if url.find('div',class_='post-snippet') else None
                if(news_url):
                    yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)

        #翻页
        if soup.find('a',class_='blog-pager-older-link'):
            next_url=soup.find('a',class_='blog-pager-older-link').get('href')
            # https://www.coolbuster.net/search/label/news?updated-max=2020-06-10T15:19:00%2B08:00&max-results=20&start=20&by-date=false
            ex='updated-max=(.*?)T(.*?)%'
            ddl=re.findall(ex,next_url,re.S)#[('2020-06-10', '15:19:00')]
            ddl=' '.join(ddl[0])#2020-06-10 15:19:00
            ddl=Util.format_time3(ddl)#1591773540
            if(self.time==None or ddl>=int(self.time)):
                yield scrapy.Request(next_url,meta=response.meta,callback=self.parse_category2)
            else:
                self.logger.info('时间截止')

    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']
        item['abstract']=response.meta['abstract']
        item['title']=soup.find('h1',class_='post-title entry-title').text.strip() if soup.find('h1',class_='post-title entry-title') else None
        

        item['body'] = ''#不能忘记初始化
        item['body']+=soup.find('div',class_="post-body entry-content").select('div')[2].text if soup.find('div',class_='post-body entry-content').select('div')[2] else None
        
        item['images']=[]
        image_list=soup.find('div',class_='separator').select('a')if soup.find('div',class_='separator') else None
        if(image_list):
            for image in image_list:
                image=image.get('href')
                item['images'].append(image)
                
        
        pub=soup.find('span',class_='updated').text.strip() if soup.find('span',class_='updated') else None     
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub
        else:
            pub=Util.format_time()
        yield item
            
