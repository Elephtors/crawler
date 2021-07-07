# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response


#author:詹婕妤
#将爬虫类名和name字段改成对应的网站名
class ParstodaySpider(scrapy.Spider):
    name = 'parstoday'
    website_id = 1155 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    allowed_domains = ['parstoday.com']
    start_urls = ['https://parstoday.com/hi']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(ParstodaySpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        soup = bs(response.text,'html.parser')
        for i in soup.select('#menu > div > div > div > ul > li'):
            url = i.find("a").get("href")
            category1 = i.find("a").text.strip()
            if url != '/' and category1 != 'Products':
                yield scrapy.Request(url,callback=self.parse2,meta={'category1':category1,'url':url,'page':1})

    def parse2(self,response):
        soup = bs(response.text,'html.parser')
        if soup.select('#itemlist > div > div.panel-body.items > ul > li') != []:
            for i in soup.select('#itemlist > div > div.panel-body.items > ul > li'):
                url = i.find('a').get("href")
                yield scrapy.Request(url,callback=self.parse_news,meta=response.meta)
            response.meta['page'] += 1
            page_url = response.meta['url'] + '?page=' + str(response.meta['page'])
            pub_time = soup.select('#itemlist > div > div.panel-body.items > ul > li')[-1].find('div','date').text
            if self.time == None or  Util.format_time3(Util.format_time2(pub_time)) >= int(self.time):
                yield scrapy.Request(page_url,callback=self.parse2,meta=response.meta)
            else:
                self.logger.info('时间截止')

    def parse_news(self,response):
        soup = bs(response.text,'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = None
        title = soup.find(class_='item-title').text.strip()
        pub_time = Util.format_time2(soup.find(class_='item-date').text.strip()) if soup.find(class_='item-date') else '0000-00-00 00:00:00'
        images = [soup.find(class_='item-media').find('img').get('src'),] if soup.find(class_='item-media').find('img') else []
        body = ''
        for p in soup.find(class_='item-text').select('p'):
            body += p.text.strip() + '\n'
        abstract = soup.find(class_='introtext').text.strip() if soup.find(class_='introtext') else body.split('\n')[0]
        item['title'] = title
        item['pub_time'] = pub_time
        item['images'] = images
        item['abstract'] = abstract
        item['body'] = body
        # self.logger.info(item)
        yield item
