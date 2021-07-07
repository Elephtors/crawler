import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class philnewsSpider(scrapy.Spider):
    name = 'philnews'
    website_id = 488 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://philnews.ph/','https://philnews.ph/news/coronavirus/','https://philnews.ph/category/educational/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(philnewsSpider, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('#ubermenu-nav-main-89265 a[href^="https://philnews.ph/category/"]'):
            if re.findall(r'https://philnews.ph/category/\S+?/\S+?$',i.attrs['href']):
                yield Request(i.attrs['href'],callback=self.parse2)

    def parse2(self, response):
        html = BeautifulSoup(response.text)
        list = response.url.split('/')
        category1 = list[4]
        if len(list)>5 and list[5] != 'page':
            category2 = list[5]
        else:
            category2 = ''
        for i in html.select('div[class="default-post-category-content post_box"] .default-category-image > a'):
            yield Request(i.attrs['href'],meta={'category1':category1,'category2':category2},callback=self.parse3)
        if html.select('.previous_posts > a') != [] and (self.time == None or Util.format_time3(Util.format_time2(html.select('div[class="default-post-category-content post_box"] .post_date')[-1].text)) >= int(self.time)):
            yield Request(html.select('.previous_posts > a')[0].attrs['href'],callback=self.parse2)
        else:
            self.logger.info('截止')

    def parse3(self, response):
        try:
            html = BeautifulSoup(response.text)
            item = DemoItem()
            item['title'] = html.select('h1.headline')[0].text
            item['category1'] = response.meta['category1']
            item['category2'] = response.meta['category2']
            item['body'] = ''
            for i in html.select('.post_content > p'):
                item['body'] += (i.text+'\n')
            if html.select('.post_content > h2') != []:
                item['abstract'] = html.select('.post_content > h2')[0].text
            item['pub_time'] = Util.format_time2(html.select('.post_date_intro > .published')[0].text)
            item['images'] = []
            for i in html.select('.post_content > figure img'):
                item['images'].append(i.attrs['src'])
        except Exception:
            pass
        yield item
