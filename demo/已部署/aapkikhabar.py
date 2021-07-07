import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

class AapkSpider(scrapy.Spider):
    name = 'aapkikhabar'
    allowed_domains = ['aapkikhabar.com']
    start_urls = ['https://aapkikhabar.com/']
    website_id = 1023  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(AapkSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    header ={
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,ja;q=0.8',
    'Connection': 'keep-alive',
    'Cookie': '_ga=GA1.1.1392112768.1609741355; _ga_external_value_=1; _ga_TKDYNPT0B7=GS1.1.1609810350.5.1.1609813210.0',
    'Host': 'aapkikhabar.com',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

    def parse(self, response):
        html = BeautifulSoup(response.text, 'html.parser')
        for i in html.select('li.home_icon~li > a'):
            url = 'https://aapkikhabar.com' + i.get('href')
            #self.logger.info(url)
            meta = {'category1': i.text, 'category2': None}
            yield Request(url, meta=meta, callback=self.parse2, headers=self.header)

        for i in html.select('li.home_icon~li')[1].select('ul a'):
            url = 'https://aapkikhabar.com' + i.get('href')
            #self.logger.info(url)
            meta = {'category1': 'प्रदेश', 'category2': i.text}
            yield Request(url, meta=meta, callback=self.parse2, headers=self.header)

    def parse2(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('#listing_main_level_top > div > div'):  # 每一页的文章
            url = 'https://aapkikhabar.com' + i.select_one('h3 > a').get('href')
            response.meta['abstract'] = soup.select_one('div.news_desc').text
            #  self.logger.info(url)
            if self.time == None or Util.format_time3(i.select_one('span.date > span ').get('data-datestring')) >= int(self.time):
                yield Request(url, callback=self.parse_item, meta=response.meta)
            else:
                flag =False
                self.logger.info('时间截止！')
        if flag:
            nextPage = soup.find("a", class_="page-numbers next last page-numbers").get("href") if soup.find("a", class_="page-numbers next last page-numbers").get("href") else None
            if nextPage:
                yield Request(url=nextPage, meta=response.meta, callback=self.parse2)

        # nextPage = soup.select('div.col-md-12 a')[-1].get('href')
        # self.logger.info(nextPage)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()

        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = soup.select_one('#detailsContentSectionWrapper > h1').text
        item['pub_time'] = soup.select('span.date span')[0].get('data-datestring')
        item['images'] = [i.get('src') for i in soup.select('div.single-image img')]
        ss = ''
        for p in soup.select('div.share-section ~ div')[0].select('p'):
            if re.match(r'Trending tweet of india', p.text):
                break
            else:
                ss += p.text
            ss += '\n'
        item['body'] = ss
        item['abstract'] = response.meta['abstract']
        return item
