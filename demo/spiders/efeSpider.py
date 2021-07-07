import scrapy
from SpainWeb.util import Util
from SpainWeb.items import SpainwebItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests

class EfeSpider(scrapy.Spider):
    name = 'efeSpider'
    allowed_domains = ['efe.com']
    start_urls = ['https://www.efe.com/efe/espana/1']
    website_id = 899  # 网站的id(必填)
    language_id = 1124  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_zjx',
        'password': 'dg_zjx',
        'db': 'dg_test'
    }

    headers = {
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(EfeSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        menu=soup.find(class_='efe-menu-secciones dropdown').select('li a')
        del menu[0]
        for i in menu:
            meta = {'category1': i.text, 'category2': None, 'title': None, 'abstract': None, 'images': None}
            url = ('https://www.efe.com/' + i.get('href'))
            yield Request(url,callback=self.parse_category,meta=meta)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        # article_hrefs = []
        # articles = soup.select('ul.lista li') if soup.select('ul.lista li') else None
        # if articles:
        #     for href in articles:
        #         article_hrefs.append(href.get('href'))
        #     for detail_url in article_hrefs:
        #         url = ('https://www.efe.com/' + detail_url.get('href'))
        #         yield Request(url,callback=self.parse_detail)
        menu=soup.select_one('ul.lista')
        for i in menu.select('li'):  # 该目录初始的文章
            url = 'https://www.efe.com/' + i.select_one('a').get('href')
            # response.meta['title'] = i.select_one('font').text
            response.meta['images'] = [i.select_one('img').get('src')]
            yield Request(url=url, meta=response.meta, callback=self.parse_detail)

        try:
            nextPage = 'https://www.efe.com/' + soup.select("li.next").select_one('a').get('href')
            yield Request(nextPage, callback=self.parse_category,meta=response.meta)
        except:
            self.logger.info('Next page no more!')


    def parse_detail(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = SpainwebItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = soup.select_one('h1.titulo').text
        time=soup.select_one('time').get('datetime')
        pub_time = time.replace('T',' ')
        pub_time = pub_time.replace('Z', '')
        item['pub_time'] = pub_time
        item['images'] = response.meta['images']
        p_list = []
        if soup.find('div', class_="texto dont-break-out").select('p'):
            all_p = soup.find('div', class_="texto dont-break-out").select('p')
            for paragraph in all_p:
                p_list.append(paragraph.text)
            body = '\n'.join(p_list)
            item['abstract'] = p_list[0]
            item['body'] = body
        return item