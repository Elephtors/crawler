
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import json

#将爬虫类名和name字段改成对应的网站名
class DemoSpider(scrapy.Spider):
    name = 'spot'
    website_id = 495 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.spot.ph/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    url = 'https://api.summitmedia-digital.com/spot/v1/channel/get{}/{}/100'

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(DemoSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self,response):
        html = BeautifulSoup(response.text)
        list = [i.attrs['href'].split('?')[0] for i in html.select('.c-nav.c-nav--sub a')[:6]]
        for i in list:
            yield Request(self.url.format(i,'0'),callback=self.parse2,meta={'category':i,'page':0})

    def parse2(self,response):
        js = json.loads(response.text)
        flag = True
        for i in js:
            try:
                if self.time == None or i['date_published'] >= int(self.time):
                    yield Request('https://www.spot.ph'+i['url'],callback=self.parse3,meta={'title':i['title'],'pub_time':i['date_published'],'abstract':i['blurb'],'images':i['image'] if 'image' in i.keys() else i['images']['main']})
                else:
                    flag = False
                    break
            except Exception:
                continue
        if flag and len(js) != 0:
            response.meta['page'] += 1
            yield Request(self.url.format(response.meta['category'],str(response.meta['page'])),callback=self.parse2,meta=response.meta)

    def parse3(self,response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.url.split('/')[3]
        item['category2'] = response.url.split('/')[4]
        item['body'] = ''
        for i in html.select('section.content > section:nth-of-type(1) p'):
            item['body'] += (i.text+'\n')
        item['abstract'] = response.meta['abstract']
        item['pub_time'] = Util.format_time(response.meta['pub_time'])
        item['images'] = [response.meta['images'],]
        yield item