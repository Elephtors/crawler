import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests
import socket

# 就 主页面之下的各类新闻，和二级目录 News 有要爬取的文章
# 发现 News 目录下的文章不属于本域名的文章


class DhindSpider(scrapy.Spider):
    name = 'dailyhindinews'
    allowed_domains = ['dailyhindinews.com']
    # start_urls = ['http://www.dailyhindinews.com/']
    website_id = 1130  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):   # 这个爬虫的时间截止有点问题
        super(DhindSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(requests.get('https://www.dailyhindinews.com/').text, 'html.parser')
        cate1_lis = [i.text for i in soup.select('h4.widget-title')[1:9]]
        # self.logger.info(cate1_lis)
        t = 0
        for i in soup.select('a.hm-viewall')[1:]: # 主页面之下的各类新闻
            meta = {'category1':cate1_lis[t], 'category2':''}
            yield Request(url=i.get('href'), meta=meta)
            t = t + 1

    def parse(self, response):
        soup = BeautifulSoup(response.text,'html.parser')
        flag = True
        for i in soup.select('article'):  # 每页的文章及其摘要
            response.meta['abstract']=i.select_one('.entry-summary p').text
            pub_time = i.select_one('time.updated').get('datetime').split('T')[0]+' '+i.select_one('time.updated').get('datetime').split('T')[1].split('+')[0]
            if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                yield Request(url=i.select_one('a').get('href'), meta=response.meta, callback=self.parse_item)
            else:
                flag = False
                self.logger.info('时间截止')
        if flag:
            try:
                nextPage = soup.find(class_='next page-numbers').get('href') if soup.find(class_='next page-numbers').get('href') else None
                yield Request(url=nextPage, meta=response.meta, callback=self.parse)
            except:
                self.logger.info('Next Page no more!')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = soup.select_one('h1.entry-title').text

        item['pub_time'] = soup.find('time', class_='entry-date published updated').get('datetime').split('T')[0]+" 00:00:00"
        item['images'] = [i.get('src') for i in soup.select('div.entry-content img')]
        ss = ''
        for p in soup.select('div.entry-content > p ')[:-1]:
            ss += p.text
            ss += '\n'
        item['body'] = ss
        item['abstract'] = response.meta['abstract']
        return item

