import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class entrepreneurSpider(scrapy.Spider):
    name = 'entrepreneur'
    website_id = 489 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.entrepreneur.com/sitemaps/main']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(entrepreneurSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        if self.time != None:
            tw = time.localtime(int(self.time))
        for i in html.select('.container > div > div > div:nth-of-type(2) > div'):
            if self.time == None or int(i.select('h2')[0].text) >= tw.tm_year:
                for j in i.select('ul a'):
                    if self.time == None or Util.month[j.text.split(' ')[0]] >= tw.tm_mon:
                        yield Request('https://www.entrepreneur.com'+j.attrs['href'],callback=self.parse1)
                    else:
                        break
            else:
                break

    def parse1(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('.nobullet.col3 a'):
            yield Request('https://www.entrepreneur.com'+i.attrs['href'],callback=self.parse2)

    def parse2(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text)
        item['title'] = html.select('.headline')[0].text
        if html.select('.valign-wrapper > a') != []:
            item['category1'] = html.select('.valign-wrapper > a')[-1].text
        item['body'] = ''
        flag = False
        for i in html.select('.art-v2-body > div:nth-of-type(1) > p'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('.art-v2-body > div > div > time')[0].text)
        item['images'] = []
        for i in html.select('.art-v2-body > div:nth-of-type(1) img'):
            item['images'].append(i.attrs['src'])
        return item