
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response


#author:甘番雨
#将爬虫类名和name字段改成对应的网站名
class puridunia(scrapy.Spider):
    name = 'puridunia'
    website_id = 1142 # 网站的id(必填)
    language_id = 1740 # 所用语言的id
    start_urls = ['https://puridunia.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(puridunia, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        meta={}
        meta['category2']=''
        soup=BeautifulSoup(response.text,'lxml')
        cat1_list=soup.select('#main-nav-menu li>a')
        for cat1 in cat1_list:
            url=cat1['href']
            meta['category1']=cat1.text
            yield scrapy.Request(url,meta=meta,callback=self.parse_category2)

    def parse_category2(self,response):
        soup=BeautifulSoup(response.text,'lxml')
        url_list=soup.select('.main-content .post-title>a')
        for url in url_list:
            news_url=url.get('href')
            yield scrapy.Request(news_url,meta=response.meta,callback=self.parse_details)

        #翻页？
        #时间截止？
        if soup.select('.date'):
            ddl=soup.select('.date')[0].text.strip()
            ddl=Util.format_time2(ddl)
            ddl=Util.format_time3(ddl)
        else:
            ddl=None
            
        if soup.find('li',class_='the-next-page') and soup.find('li',class_='the-next-page').find('a'):
            next_url=soup.find('li',class_='the-next-page').find('a').get('href')
            if(self.time==None or ddl>=int(self.time)):
                yield scrapy.Request(next_url,meta=response.meta,callback=self.parse_category2)
            else:
                self.logger.info('时间截止')

    def parse_details(self,response):
        item=DemoItem()
        soup=BeautifulSoup(response.text,'lxml')
        item['category1']=response.meta['category1']
        item['category2']=response.meta['category2']

        item['title']=soup.find('h1',class_='post-title entry-title').text.strip() if soup.find('h1',class_='post-title entry-title') else None

        item['body'] = ''#不能忘记初始化
        item['abstract']=''
        if soup.select('.entry-content p,.entry-content h3'):
            body_list=soup.select('.entry-content p,.entry-content h3')#这个写法可以同时提取到多个不同的标签
            for body in body_list:
                item['body'] += body.text.strip()
                item['body'] +='\n'
            item['abstract']=body_list[0].text.strip() 

           
        
        item['images']=[]
        image_list=soup.select('.entry-content p>img,.single-featured-image>img')if soup.select('.entry-content p>img,.single-featured-image>img') else None
        if(image_list):
            for image in image_list:
                image=image.get('src')
                item['images'].append(image)


        pub=soup.find('span',class_='date meta-item tie-icon').text.strip() if soup.find('span',class_='date meta-item tie-icon') else None
        if(pub):
            pub=Util.format_time2(pub)
            item['pub_time']=pub
        
        yield item

