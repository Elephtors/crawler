import scrapy
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time



class ManilatimesSpider(scrapy.Spider):
    name = 'Manilatimes'
    allowed_domains = ['manilatimes.net']
    start_urls = ['https://www.manilatimes.net/' ]
    website_id = 186  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(ManilatimesSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('#tdb-block-menu li a'):
            url = 'https://www.manilatimes.net' + i.get('href')
            yield scrapy.Request(url, callback=self.parse_essay, meta={'category1':i.text})
        for i in soup.select('div.td-pulldown-filter-list>li >a'):
            url = 'https://www.manilatimes.net' + i.get('href')
            yield scrapy.Request(url, callback=self.parse_essay, meta={'category1':i.text})

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('div.td-module-meta-info '):
            url = i.select_one('a').get('href')
            pub_time = Util.format_time2(i.select_one('.td-post-date').text)
            if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                response.meta['pub_time'] = pub_time
                yield scrapy.Request(url, callback=self.parse_item, meta=response.meta)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if soup.find(class_='td-icon-menu-right') and flag:
            nextPage = soup.find(class_='page-nav td-pb-padding-side').select('a')[-1].get('href')
            yield Request(nextPage, callback=self.parse_essay, meta=response.meta)


    def parse_item(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, 'html.parser')
        item['title'] = soup.select('.tdb-title-text ')[0].text
        item['category1'] = response.meta['category1']
        item['category2'] = soup.select('.tdb-entry-category ')[-1].text
        item['pub_time'] = response.meta['pub_time']
        item['abstract'] = soup.find('p').text
        ss = ""
        for s in soup.select('#fb-root ~ p'):
            ss += s.text + r'\n'
        item['body'] = ss
        item['images'] = [i.attrs['data-src'] for i in soup.select('figure > img')]
        return item


