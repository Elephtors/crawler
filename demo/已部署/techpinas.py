import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import time
from datetime import datetime

class techpinasSpider(scrapy.Spider):
    name = 'techpinas'
    website_id = 492 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.techpinas.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(techpinasSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('.section .post-outer a.read-more'):
            yield Request(i.attrs['href'],callback=self.parse1)
        if self.time == None or Util.format_time3(self.timeformat(html.select('.section .post-outer .published')[0].text)) >= int(self.time):
            yield Request(html.select('.section a.blog-pager-older-link')[0].attrs['href'])
        else:
            self.logger.info('截止')

    def parse1(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text)
        item['title'] = html.select('.post-header > h1')[0].text
        item['body'] = ''
        flag = False
        for i in html.select('.post-body.entry-content > div,.post-body.entry-content i,.post-body.entry-content > h3'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = self.timeformat(html.select('abbr.published')[0].text)
        item['images']=[]
        for i in html.select('.post-body.entry-content img'):
            item['images'].append(i.attrs['src'])
        yield item

    def timeformat(self, string):
        list1 = string.split(' ')
        list2 = list1[0].split('/')
        timetext = time.strftime("%Y-%m-%d ", datetime(int(list2[2]),int(list2[0]),int(list2[1])).timetuple())+list1[1]
        return timetext