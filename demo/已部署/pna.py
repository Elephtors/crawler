import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class PnaSpider(scrapy.Spider):
    name = 'pna'
    allowed_domains = ['www.pna.gov.ph']
    start_urls = ['https://www.pna.gov.ph/']
    website_id = 179  # 网站的id(必填)  #和websiteid=1156 重复了
    language_id = 1866  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(PnaSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('li.active ~ li a')[4:]:
            url = 'https://www.pna.gov.ph' + i.get('href')
            m = {}
            m['category1'] = i.get('href').split('/')[-1]
            yield scrapy.Request(url, callback=self.parse_essay, meta=m)

    # def parse_menu(self, response):
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     allPages = soup.select('ul.pagination  a')[-1].get('href').split('=')[-1]  # 翻页
    #     for i in range(int(allPages) + 1):
    #         url = response.url + '?p=' + str(i)
    #         yield scrapy.Request(url, callback=self.parse_essay, meta=response.meta)

    def parse_essay(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        for i in soup.select('.media-body'):  # 每页的文章
            url = 'https://www.pna.gov.ph' + i.select_one('a').get('href')
            pub_time = i.select_one('.date').text
            if self.time == None or Util.format_time3(Util.format_time2(pub_time)) >= int(self.time):
                yield scrapy.Request(url, callback=self.parse_item, meta=response.meta)
            else:
                flag = False
                self.logger.info('时间截止')
                break
        if flag:
            yield scrapy.Request('https://www.pna.gov.ph' + soup.select('.pagination a')[-2].attrs['href'], callback=self.parse_essay, meta=response.meta)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = None
        # 只好用url 里面的数字代替二级标题了。
        # 解决了，加meta 参数到Request()

        item['title'] = soup.select('div.page-header h1')[0].text
        ts = soup.select('span.date ')[0].text  # 文章时间字符串例如 ts = 'Published October 22, 2020, 4:32 PM' #下面将ts 格式化
        month = str(Util.month[ts.split(',')[0].split(' ')[1]])
        date = ts.split(',')[1] + '-' + month + '-' + ts.split(',')[0].split(' ')[2]
        date.strip()  # 去掉多余的空格
        ttt = ts.split(',')[-1].split(' ')  # ttt = ['', '4:32', 'PM']
        if ttt[-1] == 'PM':
            shi = int(ttt[-2].split(':')[0]) + 12
            time = str(shi) + ":" + ttt[-2].split(':')[1] + ":" + '00'
        else:
            shi = int(ttt[-2].split(':')[0])
            time = str(shi) + ":" + ttt[-2].split(':')[1] + ":" + '00'
        datetime = date + ' ' + time
        item['pub_time'] = datetime
        try:
            item['images'] = [i.get('src') for i in soup.select('div.page-content  img')]
        except:
            pass

        item['abstract'] = soup.select('div.page-content > p')[0].text

        ss = ''
        for i in soup.select('div.page-content > p'):
            ss += i.text + r'\n'
        item['body'] = ss
        yield item
