import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class MalayaSpider(scrapy.Spider):
    name = 'malaya'
    allowed_domains = ['malaya.com.ph']
    start_urls = ['https://malaya.com.ph/']
    website_id = 193  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(MalayaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')    # ‘https://malaya.com.ph/index.php/news/’ 这个目录下的文章动态加载。
        for i in soup.select('#menu-main_menu-1 a')[1:]:
            url = i.get('href')
            yield scrapy.Request(url, callback=self.parse_essay)

    # def parse_menu(self, response):
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     try:
    #         allPages = soup.select_one('span.pages').text.split(' ')[-1] if soup.select_one('span.pages').text else None  # 翻页
    #         if allPages:
    #             for i in range(int(allPages)):
    #                 url = response.url + 'page/' + str(i + 1) + '/'
    #                 yield scrapy.Request(url, callback=self.parse_essay)
    #         else:
    #             yield scrapy.Request(response.url, callback=self.parse_essay)
    #     except:
    #         self.logger.info(response.url+' is a wrong website!')

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.td-block-span6 '):  # 每页的文章
            url = i.select_one('a').get('href')
            pub_time = Util.format_time2(i.select_one('.td-post-date').text)
            if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                yield scrapy.Request(url, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            yield scrapy.Request(soup.select('.page-nav.td-pb-padding-side a')[-1].attrs['href'], callback=self.parse_essay)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        category = response.url.split('/')[-3].split('_')
        if len(category) == 3:
            item['category1'] = category[1]
            item['category2'] = category[2]
        else:
            item['category1'] = category[0]
            item['category2'] = category[1]

        item['title'] = soup.select_one('h1.entry-title').text

        item['pub_time'] = Util.format_time2(soup.select('span.td-post-date > time')[0].text)
        item['images'] = [i.get('data-src') for i in soup.select('div.td-post-content img')]
        item['abstract'] = soup.select('div.td-post-content > p')[0].text

        ss = ''
        for i in soup.select('div.td-post-content > p'):
            ss += i.text + r'\n'
        item['body'] = ss

        return item
