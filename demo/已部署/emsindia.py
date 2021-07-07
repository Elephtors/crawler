import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests
import socket

class EmsiSpider(scrapy.Spider):
    name = 'emsindia'
    allowed_domains = ['emsindia.com']
    #start_urls = ['https://emsindia.com/']
    website_id = 1046  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(EmsiSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(requests.get('https://emsindia.com/').text, 'html.parser')
        for i in soup.select('.dropdown > a')[:8]:
            meta = {'category1': i.text, 'category2': ''}
            yield Request(url='https://emsindia.com' + i.get('href')[1:], meta=meta)

    def parse(self, response):  # 文章列表没有时间
        soup = BeautifulSoup(response.text, 'html.parser')
        # 单独的第一篇文章
        response.meta['images'] = [i.get('src') for i in soup.select('div.inner')[-1].select('img')]
        yield Request(url='https://emsindia.com' + soup.select('div.inner')[-1].select_one('a').get('href')[1:],
                      meta=response.meta)
        for i in soup.select('.borderT>a')[:-1]:  # 每页的文章及其摘要
            response.meta['images'] = [i.select_one('img').get('src')]
            yield Request(url='https://emsindia.com' + i.get('href')[1:], meta=response.meta, callback=self.parse_item)
        # 没有翻页

    def parse_item(self, response):  # 文章时间只在具体文章页面找得到
        soup = BeautifulSoup(response.text, 'html.parser')
        s = re.findall('\d+/\d+/\d+',soup.find(attrs={'style':'font-size: 16px; font-weight:normal;'}).text)[0]
        s = s.split('/')[2]+'-'+s.split('/')[1]+'-'+s.split('/')[0]+' 00:00:00'
        if self.time == None or Util.format_time3(s) >= int(self.time):
            item = DemoItem()
            item['category1'] = response.meta['category1']
            item['category2'] = response.meta['category2']
            item['title'] = soup.select('.inner')[-1].select('h2')[0].text
            strtt = re.findall('\d+/\d+/\d+', soup.select('.inner')[-1].select('h2')[1].text)[0]  # strtt 形如 '05/01/2021'
            item['pub_time'] = s
            item['images'] = response.meta['images']
            # ss = ''
            # for p in soup.select('.inner')[-1].select('h2')[2].text.split('\n'):
            #     ss += p.text
            #     ss += '\n'
            item['body'] = soup.select('.inner')[-1].select('h2')[2].text
            item['abstract'] = soup.select('.inner')[-1].select('h2')[2].text.split('|')[0]
            return item
        else:
            self.logger.info('时间截止')
