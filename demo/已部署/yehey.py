import requests
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import json

class yehey(scrapy.Spider):# cyl
    name = 'yehey'
    # allowed_domains = ['https://yehey.com/']
    start_urls = ['https://yehey.com/']
    website_id = 1225  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(yehey, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta['category2'] = ''
        meta['url_cat'] = ''
        meta['page_number'] = ''
        html = BeautifulSoup(response.text, "html.parser")
        cat1 = html.select_one("li#menu-item-5581 a").text
        meta['category1'] = cat1  # 获取一级目录
        cat1_url = html.select_one("li#menu-item-5581 a")['href']
        yield scrapy.Request(cat1_url, meta=meta, callback=self.parse_category2)

    def parse_category2(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        cat2s = html.select("li#menu-item-5581>ul.sub-menu>li")
        for c in cat2s:
            cat2_url = c.select_one("a")['href']
            cat2 = c.select_one("a").text
            response.meta['category2'] = cat2  # 获取二级目录
            yield scrapy.Request(cat2_url, meta=response.meta, callback=self.parse_category3)

    def parse_category3(self, response):
        html = BeautifulSoup(response.text, "html.parser")
        detail_list = html.select("main#main>article")
        for d in detail_list:
            detail_url = d.select_one("h2.entry-title.th-text-md.th-mb-0 a")['href']  # 获取静态加载的url
            yield scrapy.Request(detail_url, meta=response.meta, callback=self.parse_detail)  # 处理静态的数据
        url = response.url
        ex2 = '.*?category/(.*?)/'
        url_cat = re.findall(ex2, url, re.S)[0]
        response.meta['url_cat'] = url_cat
        page_number = 3
        response.meta['page_number'] = page_number
        request_url = 'https://yehey.com/?infinity=scrolling'
        page_text = response.text
        ex = '<script type="text/javascript">.*?currentday%22%3A%22(.*?)%22%2C%22'
        currentday = re.findall(ex, page_text, re.S)[0]
        data = {
            'page': '2',
            'currentday': currentday,
            'query_args[category_name]': url_cat
        }
        yield scrapy.FormRequest.from_response(response, url=request_url, formdata=data, method='POST',
                                               meta=response.meta, callback=self.parse_category4)

    def parse_category4(self, response):
        request_url = 'https://yehey.com/?infinity=scrolling'
        url_cat = response.meta['url_cat']
        page_number = response.meta['page_number']
        dic = {'type': 'empty'}
        if json.loads(response.body) == dic:
            pass
        else:
            if 'currentday' in json.loads(response.body).keys():
                currentday = json.loads(response.body)['currentday']
                data = {
                    'page': str(page_number),
                    'currentday': currentday,
                    'query_args[category_name]': url_cat
                }
                if 'postflair' in json.loads(response.body).keys():
                    details = json.loads(response.body)['postflair'].keys()
                    for i in details:
                        yield scrapy.Request(i, meta=response.meta, callback=self.parse_detail)
                if 'html' in json.loads(response.body).keys():
                    html = json.loads(response.body)['html']
                    html = BeautifulSoup(html, "html.parser")
                    ddl = html.select("article time")[0]['datetime']
                    ddl = re.split('T|\+', ddl)  # ['2021-01-30', '23:00:00', '08:00']
                    ddl = ddl[0] + ' ' + ddl[1]  # 2021-01-30 23:00:00
                    ddl = Util.format_time3(ddl)
                else:
                    ddl = None
                if (self.time == None or ddl >= int(self.time)):
                    response.meta['page_number'] = response.meta['page_number'] + 1
                    yield scrapy.FormRequest(url=request_url, formdata=data, method='POST',
                                                               meta=response.meta, callback=self.parse_category4)
                else:
                    self.logger.info('时间截止')
                    pass



    def parse_detail(self,response):
        item = DemoItem()
        html = BeautifulSoup(response.text, 'html.parser')
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        if html.find('h1', class_='entry-title th-mb-0 sm:th-text-8xl th-text-4xl').text.strip():  # 获取标题
            item['title'] = html.find('h1', class_='entry-title th-mb-0 sm:th-text-8xl th-text-4xl').text.strip()
        item['body'] = ''  # 获取正文内容
        if html.select("div.entry-content.th-content p"):
            bodies = html.select("div.entry-content.th-content p")
            item['abstract'] = bodies[0].text  # 获取摘要
            # for b in bodies:
            #     item['body'] += b.text.strip()
            #     item['body'] += "\n"
            b_list = [b.text.strip() for b in bodies]
            item['body'] = '\n'.join(b_list)
        item['images'] = []  # 获取图片链接
        if html.select_one("header#primary-header img") is not None:  # 获取单独在标题的图片
            image_one = html.select_one("header#primary-header img")['src']
            item['images'].append(image_one)
        if html.select("div.entry-content.th-content a>img"):  # 获取在段落中的图片
            imgaes = html.select("div.entry-content.th-content a>img")
            for i in imgaes:
                item['images'].append(i['src'])
        if html.select_one("time.entry-date.published") is not None:  # 获取发布时间
            pub = html.select_one("time.entry-date.published")['datetime']
            pub_time = re.split('T|\+', pub)  # datetime="2021-01-30T23:00:00+08:00"
            pubtime = pub_time[0] + ' ' + pub_time[1]  # ['2021-01-30', '23:00:00', '08:00']
            item['pub_time'] = pubtime  # 2021-01-30 23:00:00
        yield item