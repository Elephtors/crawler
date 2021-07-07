import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import json
import time
import requests
import socket

class unboxSpider(scrapy.Spider):
    name = 'unbox'
    website_id = 485 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    # start_urls = ['https://www.example.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    data = {
        'action': 'tie_blocks_load_more',
        'block[order]': 'latest',
        'block[source]': 'id',
        'block[number]': '10',
        'block[pagi]': 'load-more',
        'block[excerpt]': 'true',
        'block[post_meta]': 'true',
        'block[read_more]': 'true',
        'block[breaking_effect]': 'reveal',
        'block[sub_style]': 'big',
        'block[style]': 'default',
        'block[title_length]': '',
        'block[excerpt_length]': '',
        'block[media_overlay]': '',
        'block[read_more_text]': '',
        'page': '1',
        'width': 'single',
        }

    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
        }

    def __init__(self, time=None, *args, **kwargs):
        super(unboxSpider, self).__init__(*args, **kwargs)
        self.time = time

    def start_requests(self):
        socket.setdefaulttimeout(30)
        for i in range(1,5000):
            self.data['page'] = str(i)
            html = BeautifulSoup(json.loads(json.loads(requests.post('https://www.unbox.ph/wp-admin/admin-ajax.php',data=self.data,headers=self.header,proxies={"http": "http://192.168.235.227:8888","https": "https://192.168.235.227:8888"}).text))['code'])
            for j in html.select('li > a'):
                yield Request(j.attrs['href'])
            if self.time != None and Util.format_time3(Util.format_time2(html.select('li .date.meta-item.tie-icon')[-1].text)) < int(self.time):
                break


    def parse(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['title'] = html.select('.entry-header > h1')[0].text
        item['body'] = ''
        flag = False
        for i in html.select('div[class="entry-content entry clearfix"] p,em,strong,h3'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('span[class="date meta-item tie-icon"]')[0].text)
        item['images'] = []
        for i in html.select('div[class="entry-content entry clearfix"] img'):
            item['images'].append(i.attrs['src'])
        yield item
