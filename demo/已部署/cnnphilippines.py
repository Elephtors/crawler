import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re

class cnnphilippinesSpider(scrapy.Spider):
    name = 'cnnphilippines'
    website_id = 449 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.cnnphilippines.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(cnnphilippinesSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('#topNavbar > ul > li > a')[1:7]:
            yield Request('http://www.cnnphilippines.com'+i.attrs['href'],callback=self.parse1)

    def parse1(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('section.row.container-padding-10 a'):
            yield Request('https://www.cnnphilippines.com'+i.attrs['href'],callback=self.parse2)
        for i in html.select('.row.carousel-body .cpmedium-header a'):
            yield Request('https://www.cnnphilippines.com'+i.attrs['href'],callback=self.parse2)

    def parse2(self, response):
        item = DemoItem()
        html = BeautifulSoup(response.text)
        list = response.url.split('/')
        item['title'] = html.select('.title')[0].text
        item['category1'] = list[3]
        if re.findall(r'\d+',list[4]) == []:
            item['category2'] = list[4]
        item['body'] = ''
        flag = False
        for i in html.select('#content-body-244757-498257 > p'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        if html.select('.dateLine > p') != []:
            item['pub_time'] = Util.format_time2(html.select('.dateLine > p')[0].text)
        elif html.select('.dateString') != []:
            item['pub_time'] = Util.format_time2(html.select('.dateString')[0].text)
        if html.select('.margin-bottom-15 img') != []:
            item['images'] = ['https://www.cnnphilippines.com'+html.select('.margin-bottom-15 img')[0].attrs['src'],]
        yield item