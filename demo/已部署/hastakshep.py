import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class HastakshepSpider(scrapy.Spider):
    name = 'hastakshep'
    allowed_domains = ['hastakshep.com']
    website_id = 1055  # 网站的id(必填)
    start_urls = ['https://www.hastakshep.com/']
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    hindi_time_ago ={
        'महीना': 'months',
        'घंटे': 'hours',
        'मिन': 'mins',
        'साल': 'years',
        'सप्ताह': 'weeks',
        'दिन': 'days'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(HastakshepSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#menu-header > li > a'):
            if re.findall('category',i.get('href')):
                meta = {'category1': i.text, 'category2': None}
                yield Request(url=i.get('href'), meta=meta, callback=self.parse_essay)
            else:
                print('Wrong Url:', i.get('href'))
                continue

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.find_all(class_='amp-wp-content amp-loop-list'):
            tt = i.select_one('.featured_time ').text.split()  # 形如 ['2','दिन','ago' ]
            try:
                pub_time = tt[0]+' '+self.hindi_time_ago[tt[1]]+' '+tt[2] # 形如 '2 days ago'
            except:
                pub_time = Util.format_time(0)
            if self.time is None or Util.format_time3(Util.format_time2(pub_time)) >= int(self.time):  # 未截止，True
                response.meta['title'] = i.select_one('h2').text
                response.meta['abstract'] = i.select_one('.large-screen-excerpt-design-3').text
                response.meta['pub_time'] = Util.format_time2(pub_time)
                response.meta['images'] = [i.select_one('amp-img').get('src')]
                yield Request(url=i.select_one('a').get('href'), meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            nextPage = soup.select_one('#pagination a').get('href', 'Next Page No More')
            yield Request(nextPage, meta=response.meta, callback=self.parse_essay)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['abstract'] = response.meta['abstract']
        item['images'] = response.meta['images']
        item['category2'] = response.meta['category2']
        ss = ''
        for i in soup.find(class_='amp-wp-content the_content').find_all('p'):
            ss += i.text + '\n'
        item['body'] = ss
        item['pub_time'] = response.meta['pub_time']
        return item