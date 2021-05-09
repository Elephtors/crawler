# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request

def time_font(time):
    #Mar 13, 2021
    # - 23:32
    #%Y-%m-%d %H:%M:%S
    time_past = time[0]
    month = time_past.split(' ')[0]
    day = time_past.split(' ')[1].strip(',')
    year = time_past.split(' ')[2]
    if month == 'Jan':
        month = '01'
    elif month == 'Feb':
        month = '02'
    elif month == 'Mar':
        month = '03'
    elif month == 'Apr':
        month = '04'
    elif month == 'May':
        month = '05'
    elif month == 'Jun':
        month = '06'
    elif month == 'Jul':
        month = '07'
    elif month == 'Aug':
        month = '08'
    elif month == 'Sep':
        month = '09'
    elif month == 'Oct':
        month = '10'
    elif month == 'Nov':
        month = '11'
    else:
        month = '12'
    return year + '-' + month + '-' + day + ' ' + time[2] + ':00'

def time_font_2(past_time):
    #Mar 29, 2021
    year = past_time.split(' ')[2]
    day = past_time.split(' ')[1].strip(',')
    month = past_time.split(' ')[0]
    if month == 'Jan':
        month = '01'
    elif month == 'Feb':
        month = '02'
    elif month == 'Mar':
        month = '03'
    elif month == 'Apr':
        month = '04'
    elif month == 'May':
        month = '05'
    elif month == 'Jun':
        month = '06'
    elif month == 'Jul':
        month = '07'
    elif month == 'Aug':
        month = '08'
    elif month == 'Sep':
        month = '09'
    elif month == 'Oct':
        month = '10'
    elif month == 'Nov':
        month = '11'
    else:
        month = '12'
    return year + '-' + month + '-' + day + ' 00:00:00'

class poorvanchalmedia(scrapy.Spider):
    name = 'poorvanchalmedia'
    website_id = 1144 # 网站的id(必填)
    language_id = 1740 # 所用语言的id
    start_urls = ['https://www.poorvanchalmedia.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(poorvanchalmedia, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text, 'lxml')
        for i in html.find('ul', class_='nav navbar-nav').find_all('li')[1:]:
            if i.find('a', class_='dropdown-toggle disabled') != None:
                yield Request(i.find('a',class_='dropdown-toggle disabled').get('href'),callback=self.parse_2)

    def parse_2(self,response, **kwargs):
        page = BeautifulSoup(response.text, 'lxml')
        category1 = page.find('h1', class_='page-title').text
        for i in page.find('div', id='content').find_all('div', class_='post-item-image'):
            images = i.find('img').get('data-src')
            yield Request(i.find('a').attrs['href'],callback=self.parse_3,meta={'category1':category1,'images':images})
        if page.find('ul', class_='pagination').find('li', class_='next') is not None:
            next_url = page.find('ul', class_='pagination').find('li', class_='next').find('a').get('href')
            last_time = time_font_2(page.find('div', id='content').find_all('div', class_='post-item')[-1].find('p',class_='post-meta').text.strip('\n'))
            if self.time is None or Util.format_time3(last_time) >= int(self.time):
                yield Request(next_url,callback=self.parse_2)
            else:
                self.logger.info('截止')

    def parse_3(self,response,**kwargs):
        new_soup = BeautifulSoup(response.text, 'lxml')
        item = DemoItem()
        item['images'] = response.meta['images']
        item['category1'] = response.meta['category1']
        item['title'] = new_soup.find('h1', class_='title').text
        item['body'] = ''
        for i in new_soup.find('div', class_='post-text show_data_between_para').find_all('p'):
            item['body'] += i.text
        item['pub_time'] = time_font(new_soup.find('div',class_='post-details-meta-date').find('span',class_='sp-left').text.strip('\n').split(' '))
        item['abstract'] = new_soup.find('div', class_='post-text show_data_between_para').find_all('p')[0].text
        yield item