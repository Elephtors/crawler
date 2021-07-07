import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class yugatechSpider(scrapy.Spider):
    name = 'yugatech'
    website_id = 444 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.yugatech.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(yugatechSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('div[class="pad group"] > article .tab-item-title > a'):
            yield Request(i.attrs['href'],callback=self.parse2)
        if self.time == None or Util.format_time3(Util.format_time2(html.select('article .post-byline')[-1].text)) >= int(self.time):
            yield Request(html.select('ul.group li.next.right a')[-1].attrs['href'])
        else:
            self.logger.info('截止')

    def parse2(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        list = response.url.split('/')
        item['title'] = html.select('.post-title')[0].text
        item['category1'] = list[3]
        item['body'] = ''
        flag = False
        for i in html.select('.entry-inner > p'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('.post-byline')[0].text)
        item['images'] = []
        for i in html.select('.entry-inner > p img'):
            item['images'].append(i.attrs['src'])
        yield item
