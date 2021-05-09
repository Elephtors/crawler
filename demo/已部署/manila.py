import json

import scrapy
from bs4 import BeautifulSoup
from scrapy import Request
import re
from demo.items import DemoItem
from demo.util import Util


class ManilaSpider(scrapy.Spider):
    name = 'manila'
    allowed_domains = ['manilastandard.net']
    start_urls = ['https://manilastandard.net']
    website_id = 190  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    url = 'https://manilastandard.net/api/sub/articles?page={}&category={}&column=0&totItems={}&currentItems={}&exemption=0'

    def __init__(self, time=None, *args, **kwargs):
        super(ManilaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):  # 进入一级目录
        soup = BeautifulSoup(response.text, 'html.parser')
        menu1 = soup.select('nav>div:nth-child(1)>div.col-xs-12  a')
        menu2 = soup.select('nav>div:nth-child(2)>div.col-xs-12  a')[:-1]
        meta1 = {}
        meta2 = {}
        for i in menu1:
            meta1['cate1'] = i.text
            try:
                yield Request(i.get('href'), callback=self.parse2, meta=meta1)
            except:
                self.logger.info('Wrong url: '+i.get('href'))
        for i in menu2:
            meta2['cate1'] = i.text
            yield Request(i.get('href'), callback=self.parse2, meta=meta2)

    def parse2(self, response):  # 进入二级目录
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            menu3 = soup.select('div.page-category-contents tr td a.category-name')
            meta = {}
            for i in menu3:
                meta['cate2'] = i.get('title')
                meta['cate1'] = response.meta['cate1']
                yield Request(i.get('href'), meta=meta, callback=self.parse3)
        except:
            self.logger.info('No more the next category')
            Request(response.url, callback=self.parse3, meta=response.meta)

    def parse3(self, response):  # 到达文章列表页面，分析翻页api实现翻页,并且yield 每篇文章给parse_item()
        soup = BeautifulSoup(response.text, 'html.parser')
        tt = soup.select('div.page-category-contents ~ div > button')[0].get('onclick')  # 含有四个parameter的字符串
        param_lis = re.findall(r'\d+, \d+, \d+, \d+', tt)[0].split(',')  # 匹配得到[category,column,totItems,currentItems]
        response.meta['category'] = param_lis[0]
        response.meta['page'] = 1
        response.meta['totItems'] = param_lis[2]
        url = self.url.format(response.meta['page'],response.meta['category'],response.meta['totItems'],str((response.meta['page'] - 1) * 10))
        yield Request(url,callback=self.parse4,meta=response.meta)

    def parse4(self, response):
        flag = True
        essaysList = BeautifulSoup(json.loads(response.text)['data'], 'html.parser').select('div.articlecontext')
        for i in essaysList:
            pub_time = Util.format_time2(re.findall(r'\d+ \w+ ago',i.text)[0])
            if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                yield Request(i.select_one('a').get('href'), callback=self.parse_item, meta=response.meta)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag and (response.meta['page'] - 1) * 10 <= int(response.meta['totItems']):
            response.meta['page'] += 1
            yield Request(self.url.format(response.meta['page'],response.meta['category'],response.meta['totItems'],str((response.meta['page'] - 1) * 10)), callback=self.parse4, meta=response.meta)


    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()

        item['category1'] = response.meta['cate1']
        item['category2'] = response.meta['cate2']

        item['title'] = soup.select_one('h1.custom-article-title').text

        item['pub_time'] = Util.format_time2(
            re.findall(r'\w+ \d+, \d+',
                       soup.select_one('div.ts-article-author-container').text)[0])

        item['images'] = [i.get('src') for i in soup.select('figure.image img')]
        item['abstract'] = soup.select('div.article-description-relative ~ div')[1].text.split('\\')[0]

        # ss = ''
        # for i in soup.select('#bcrum ~div > p'):
        #     ss += i.text + '\n'
        # for i in soup.select('#bcrum ~ div >ol'):
        #     ss += i.text + '\n'
        item['body'] = soup.select('div.article-description-relative ~ div')[1].text

        yield item
