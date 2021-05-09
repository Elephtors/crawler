import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import execjs
import requests
import socket

class ptvnewsSpider(scrapy.Spider):
    name = 'ptvnews'
    website_id = 445 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://ptvnews.ph/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(ptvnewsSpider, self).__init__(*args, **kwargs)
        self.time = time

    def html_get(self, response):
        socket.setdefaulttimeout(30)
        header = self.headers
        js = re.findall(r'<script>(.+)</script>',response.text)[0]
        ctx1 = execjs.compile('function fun(){'+js.replace('e(r)','return r')+'}') 
        ctx2 = execjs.compile('function fun(){'+js.replace('e(r);',ctx1.call('fun')).replace('document.cookie','num').replace('location.reload()','return num')+'}')
        header['cookie'] = ctx2.call('fun')
        self.logger.info(header['cookie'])
        return requests.get(response.url,headers=header,proxies={"http": "http://192.168.235.227:8888","https": "https://192.168.235.227:8888"})

    def parse(self, response):
        res = response
        while True:
            if re.findall(r'Javascript is required. Please enable javascript before you are allowed to see this page.',res.text) == []:
                break
            res = self.html_get(res)
        html = BeautifulSoup(res.text)
        for i in html.select('.sub-menu > li > a')[:12]:
            yield Request(i.attrs['href'],callback=self.parse1)
        yield Request('https://ptvnews.ph/category/sports/',callback=self.parse1)
        yield Request('https://ptvnews.ph/category/business/',callback=self.parse1)

    def parse1(self, response):
        res = response
        while True:
            if re.findall(r'Javascript is required. Please enable javascript before you are allowed to see this page.',res.text) == []:
                break
            res = self.html_get(res)
        html = BeautifulSoup(res.text)
        list = response.url.split('/')
        category1 = list[4]
        if list[5] != 'page':
            category2 = list[5]
        for i in html.select('.td-ss-main-content .td-block-span6 h3 > a'):
            yield Request(i.attrs['href'],meta={'category1':category1,'category2':category2},callback=self.parse2)
        if self.time == None or Util.format_time3(Util.format_time2(html.select('.td-ss-main-content time')[-1].text)) >= int(self.time):
            yield Request(html.select('.page-nav.td-pb-padding-side > a')[-1].attrs['href'],callback=self.parse1)
        else:
            self.logger.info('截止')

    def parse2(self, response):
        res = response
        while True:
            if re.findall(r'Javascript is required. Please enable javascript before you are allowed to see this page.',res.text) == []:
                break
            res = self.html_get(res)
        html = BeautifulSoup(res.text)
        item = DemoItem()
        item['title'] = html.select('.entry-title')[0].text
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['body'] = ''
        flag = False
        for i in html.select('.td-post-content > p'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('time[class="entry-date updated td-module-date"]')[0].text)
        if html.select('.td-post-featured-image img') != []:
            item['images'] = [html.select('.td-post-featured-image img')[0].attrs['src'],]
        item['html'] = res.text
        yield item
