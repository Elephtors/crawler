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
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
    }

    def parse(self, response):  # 进入一级目录
        soup = BeautifulSoup(response.text, 'html.parser')
        menu1 = soup.select('nav>div:nth-child(1)>div.col-xs-12  a')
        menu2 = soup.select('nav>div:nth-child(2)>div.col-xs-12  a')[:-1]
        meta1 = {}
        meta2 = {}
        for i in menu1:
            meta1['cate1'] = i.text
            yield Request(i.get('href'), callback=self.parse2, meta=meta1)
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
            Request(response.url, callback=self.parse3, meta=meta)

    def parse3(self, response):  # 到达文章页面，分析翻页api实现翻页
        soup = BeautifulSoup(response.text, 'html.parser')
        tt = soup.select('div.page-category-contents ~ div > button')[0].get('onclick')  # 含有四个parameter的字符串
        param_lis = re.findall(r'\d+, \d+, \d+, \d+', tt)[0].split(',')  # 匹配得到[category,column,totItems,currentItems]
        allPages = str(int((int(param_lis[2]) + 10) / 10))
        category = param_lis[0]

        for p in range(int(allPages)):
            currentItems = str((p + 1) * 10)
            url = 'https://manilastandard.net/api/sub/articles?page=' + str(p + 1) + '&category=' + category + \
                  '&column=0&totItems=' + param_lis[2] + '&currentItems=' + currentItems + '&exemption=0'
            yield Request(url, callback=self.parse4, meta=response.meta)

    def parse4(self, response):
        essaysList = BeautifulSoup(
            json.loads(
                response.text)['data'], 'html.parser').select('div.articleimg a')
        for i in essaysList:
            yield Request(i.get('href'), callback=self.parse_item, meta=response.meta)

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
