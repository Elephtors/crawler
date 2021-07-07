import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time



class FiliSpider(scrapy.Spider):
    name = 'fili'
    allowed_domains = ['filipinoexpress.com']
    start_urls = ['http://www.filipinoexpress.com/']
    website_id = 182  # 网站的id(必填)
    language_id = 2266  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(FiliSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#s5_nav > li.active ~li > span >span >a')[:5]:
            url = 'http://www.filipinoexpress.com' + i.get('href')
            yield scrapy.Request(url, callback=self.parse_essay)

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('div.blog > div ')[:-2]:  # 每页的文章
            for j in range(2):
                url = 'http://www.filipinoexpress.com' + i.select('h2>a')[j].get('href')
                tt = i.select('.published ')[j].text.split(',')[1].split()
                pub_time = Util.format_time2(tt[1]+" "+tt[0]+" "+tt[2])
                if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                    yield scrapy.Request(url, callback=self.parse_item)
                else:
                    flag = False
                    self.logger.info('时间截止')
        if flag:
            yield scrapy.Request('http://www.filipinoexpress.com'+soup.select('.pagination .pagination-next a')[0].attrs['href'], callback=self.parse_essay)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        category = soup.select('div.breadcrumbs > a')
        if len(category) == 1:
            item['category1'] = category[0].text
            item['category2'] = None
        else:
            item['category1'] = category[0].text
            item['category2'] = category[1].text

        item['title'] = soup.select('div.breadcrumbs > span')[-1].text
        ttt = soup.select('dd.published')[0].text.split(',')[1].split(' ')[1:]
        datetime = ttt[2] + '-' + str(Util.month[ttt[1]]) + '-' + ttt[0] + ' ' + ttt[-1][:5] + ':00'
        item['pub_time'] = datetime
        item['images'] = None
        item['abstract'] = soup.select('div.item-page > p')[0].text

        ss = ''
        for i in soup.select('div.item-page > p'):
            ss += i.text + r'\n'
        item['body'] = ss

        yield item
