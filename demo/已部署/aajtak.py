import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import socket

class AajtSpider(scrapy.Spider):
    name = 'aajtak'
    allowed_domains = ['aajtak.in']
    start_urls = ['http://aajtak.in/']
    website_id = 467  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    hindi_month ={
        'जनवरी': 'Jan',
        'फ़रवरी': 'Feb',
        'मार्च': 'March',
        'अप्रैल': 'April',
        'मई': 'May',
        'जून': 'June',
        'जुलाई': 'July',
        'अगस्त': 'August',
        'सितंबर':'September',
        'अक्टूबर':'October',
        'नवंबर':'November',
        'दिसंबर':'December'
    }
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }
    params = {
               'id': '1',
               'type': 'story/photo_gallery/video/breaking_news',  # 不能有空格，否则提交params参数时，会有错误
               'path': '/india'
    }
    api_url = 'https://www.aajtak.in/ajax/load-more-widget?id=1&type=story/photo_gallery/video/breaking_news&path=/india'

    # for i in soup.select('.content-area > div')[4:7]:
    #     ...
    #     for j in i.select('a'):
    #         ...
    #     print(j.get('href'))

    def __init__(self, time=None, *args, **kwargs):
        super(AajtSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):  # 进入一级目录
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(requests.get('https://www.aajtak.in/').text, 'html.parser')
        for i in soup.select('.at-menu li a')[2:-1]:
            yield Request(url=i.get('href'),meta={'category1':i.text},callback=self.parse)

    def parse(self, response):  # 进入二级目录
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('.widget-title a'):   # 静态加载的二级目录
            response.meta['category2'] = i.text
            yield Request(url=i.get('href'),meta=response.meta, callback=self.parse_essay)
        try:  # 尝试动态加载,（有的二级目录没有动态加载
            i = 1
            self.params['path'] = response.replace('https://www.aajtak.in','')
            while(True):
                self.params['id'] = str(i)
                i += 1
                api_rq = requests.get(self.api_url, params=self.params, headers=self.headers)
                api_rq.raise_for_status()
                soup = BeautifulSoup(api_rq.text, 'html.parser')
                for i in soup.select('.widget-title a'):  # 动态加载的二级目录
                    response['category2'] = i.text
                    yield Request(url=i.get('href'), meta=response.meta, callback=self.parse_essay)
        except:
            self.logger.info('No more dynamic category2 loading!')

    def parse_essay(self, response):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.widget-listing '):  # 静态文章列表
            response.meta['title'] = i.select_one('a').get('title')
            mm = i.select_one('h5').text  # 形如 '09 जनवरी 2021'
            ss = self.hindi_month[mm.split()[1]] + ' ' + mm.split()[0] + ' ' + mm.split()[2]  # ss 形如 'Jan 09 2021'
            response.meta['pub_time'] = Util.format_time2(ss)
            if self.time == None or Util.format_time3(Util.format_time2(ss)) >= int(self.time):
                yield Request(url=i.select_one('a').get('href'), meta=response.meta, callback=self.parse_item)
            else:
                self.logger.info('时间截止！')
        try:  # 尝试动态加载,（有的二级目录没有动态加载
            i = 1
            self.params['path'] = response.replace('https://www.aajtak.in', '')
            while True:
                if flag:
                    self.params['id'] = str(i)
                    i += 1
                    api_rq = requests.get(self.api_url, params=self.params, headers=self.headers)
                    if api_rq.status_code == 200:
                        soup = BeautifulSoup(api_rq.text, 'html.parser')
                        for i in soup.select('.widget-listing '):  # 动态加载的二级目录
                            response.meta['title'] = i.select_one('a').get('title')
                            mm = i.select_one('h5').text  # 形如 '09 जनवरी 2021'
                            ss = self.hindi_month[mm.split()[1]]+' '+ mm.split()[0]+' '+mm.split()[2]  # ss 形如 'Jan 09 2021'
                            response.meta['pub_time'] = Util.format_time2(ss)
                            if self.time == None or Util.format_time3(Util.format_time2(ss)) >= int(self.time):
                                yield Request(url=i.select_one('a').get('href'),meta=response.meta, callback=self.parse_item)
                            else:
                                flag = False
                                self.logger.info('时间截止！')
        except:
            self.logger.info('No more dynamic news loading!')

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['title'] = response.meta['title']
        item['pub_time'] = response.meta['pub_time']
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if re.match('^\S+/story/',response.url):  # 图文新闻
            item['abstract'] = soup.select_one('div.sab-head-tranlate-sec ').text
            try:
                item['images'] = [i.get('src') for i in soup.select_one('.main-img img')].append(soup.select_one('.embedded-entity img').get('src'))
            except:
                item['images'] = [i.get('src') for i in soup.select_one('.main-img img')]

            ss = ''
            for j in soup.select('.story-with-main-sec p'):
                ss += j.text + '\n'
                item['body'] = ss
        elif re.match('^\S+/photo/', response.url):  # 图片新闻
            item['abstract'] = soup.select_one('div.photo-Detail-LHS-Heading ').text
            ss = ''
            for i in soup.select('.photo-detail-text p'):
                ss += i.text + '\n'
            item['body'] = ss
            item['images'] = [i.get('src') for i in soup.select('.big-photo img')]
        else:  # 视频新闻
            ss = ''
            for i in soup.select('.common-area p'):
                ss += i.text + '\n'
            item['body'] = ss
            item['abstract'] = ss
            item['images'] = None
        return item




