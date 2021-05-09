import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests
import json
import socket

class HbarSpider(scrapy.Spider):
    name = 'apkaakhbar'
    allowed_domains = ['apkaakhbar.com']
    # start_urls = ['http://apkaakhbar.com/']
    website_id = 1059  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }
    data = {
        'action': 'td_ajax_loop',
        'loopState[sidebarPosition]': '',
        'loopState[moduleId]': '6',
        'loopState[currentPage]': '2',  # 翻页变
        'loopState[max_num_pages]': '4',  # 每个栏目不一样
        'loopState[atts][category_id]': '21',  # 每个栏目不一样  # 其他不变
        'loopState[atts][offset]': '2',
        'loopState[ajax_pagination_infinite_stop]': '0',
        'loopState[server_reply_html_data]': ''
    }
    post_url = 'https://apkaakhbar.com/wp-admin/admin-ajax.php?td_theme_name=Newspaper&v=8.0'

    def __init__(self, time=None, *args, **kwargs):
        super(HbarSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        socket.setdefaulttimeout(30)
        #yield Request(url='https://apkaakhbar.com/', callback=self.parse2, meta={'category1': 'Home'})
        #yield Request(url='https://apkaakhbar.com/', callback=self.parse_home, meta={'category1': 'Home'})
        soup = BeautifulSoup(requests.get(url='https://apkaakhbar.com/', headers=self.headers).text, 'html.parser')
        for i in soup.select('#menu-td-demo-header-menu-1 li a')[1:-1]:
            meta = {'category1': i.text}
            yield Request(url=i.get('href'), meta=meta, callback=self.parse)

    def judge_pub_time(self, url):  # 单独requests 拿pub_time
        socket.setdefaulttimeout(30)
        if self.time == None:
            return True
        tt = BeautifulSoup(requests.get(url, headers=self.headers).text,
                           'html.parser').find(class_='entry-date updated td-module-date').text  # tt 形如January 11, 2021
        pub_time = Util.format_time2(tt)
        if self.time == None or Util.format_time3(pub_time) >= int(self.time):
            return True
        else:
            return False

    def parse(self, response):
        flag1 = True
        flag2 = True
        if response.url != self.post_url:  # 若不是post返回的response 可以用BeautiSoup解析，否则要经过json过滤再用BS解析
            soup = BeautifulSoup(response.text, 'html.parser')  # 一下三行 得到并初始化，动态翻页post请求的三个data的参数
            response.meta['max_num_pages'] = \
            re.findall(r'tdAjaxLoop.loopState.max_num_pages = \d+', response.text)[-1].split()[-1]
            response.meta['currentPage'] = '1'    # FormRequest(formdata=self.data)这里的formdata是dict，不能存在数字，如有数字用引号括起来；
            response.meta['category_id'] = re.findall(r"'category_id':\d+", response.text)[0].split(':')[-1]
            self.data['loopState[atts][category_id]'] = response.meta['category_id']
            self.data['loopState[max_num_pages]'] = response.meta['max_num_pages']
            for i in soup.select('.td-big-grid-wrapper > div'):  # 两个大照片的文章
                response.meta['title'] = i.select_one('a').get('title')
                if self.judge_pub_time(i.select_one('a').get('href')):
                    yield Request(url=i.select_one('a').get('href'), callback=self.parse_item, meta=response.meta)
                else:
                    flag1 = False
                    self.logger.info('时间截止')
                if flag1 is False:
                    break
        else:
            soup = BeautifulSoup(json.loads(response.text)["server_reply_html_data"],
                                 'html.parser')  # post请求返回的response，用json搭桥，变成bs对象
            for i in soup.select('div.td-block-span6 a'):  # 从动态加载的第1页开始拿文章
                response.meta['title'] = i.get('title')
                if self.judge_pub_time(i.get('href')):
                    yield Request(url=i.get('href'), callback=self.parse_item, meta=response.meta)
                else:
                    flag2 = False
                    self.logger.info('时间截止')
                if flag2 is False:
                    break
        if flag2:  # 动态翻页
            if int(response.meta['currentPage']) <= int(response.meta['max_num_pages']):
                self.data['loopState[currentPage]'] = response.meta['currentPage']
                response.meta['currentPage'] = str(int(response.meta['currentPage']) + 1)  # 当前页加一，传给 下一次post
                yield scrapy.FormRequest(url=self.post_url, meta=response.meta, method='POST', formdata=self.data)

    def parse2(self, response):  # 主页的文章，和翻页的文章
        soup = BeautifulSoup(response.text, 'html.parser')
        flag1 = True
        flag2 = True
        for i in soup.select('.meta-info-container a'):  # 大照片新闻
            response.meta['title'] = i.get('title')
            if self.judge_pub_time(i.get('href')):
                yield Request(url=i.get('href'), callback=self.parse_item, meta=response.meta)
            else:
                flag1 = False
                self.logger.info('时间截止')
            if flag1 is False:
                break
        for i in soup.select('.td-block-span4 a'):  # 大照片下面模块的新闻
            response.meta['title'] = i.get('title')
            if self.judge_pub_time(i.get('href')):
                yield Request(url=i.get('href'), callback=self.parse_item, meta=response.meta)
            else:
                flag2 = False
                self.logger.info('时间截止')
            if flag2 is False:
                break

    def parse_home(self, response):  # 首页最底下翻页下新闻
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.td-block-span6 a'):  # 一页的新闻
            response.meta['title'] = i.get('title')
            if self.judge_pub_time(i.get('href')):
                yield Request(url=i.get('href'), callback=self.parse_item, meta=response.meta)
            else:
                flag = False
                self.logger.info('时间截止')
            if flag is False:
                break
        if flag:  # 未到截止时间就翻页
            try:
                nextPage = soup.select_one('span.current ~ a').get('href')
                yield Request(url=nextPage, callback=self.parse_home, meta=response.meta)
            except:
                self.logger.info('Next page no more')

    def parse_item(self, response):  # 文章时间只在具体文章页面找得到
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['images'] = [i.get('src') for i in soup.select('article img')[:-3]]
        item['title'] = response.meta['title']
        item['category1'] = response.meta['category1']
        item['category2'] = None
        tt = soup.find(class_='entry-date updated td-module-date').text  # tt 形如January 11, 2021
        item['pub_time'] = Util.format_time2(tt)
        abstract = ''
        for i in soup.select('strong '):
            abstract += i.text
        item['abstract'] = abstract
        item['body'] = soup.findChildren(class_='td-post-content')[0].get_text()
        return item
