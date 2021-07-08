import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
import requests

def time_font(time_past):
    #调整时间格式
    #Mon, 04 Jan 2021 16:50:33
    #%Y-%m-%d %H:%M:%S
    time = re.findall('.*?Date:(.*?)      .*?' , time_past)[0]
    day = time.split(' ')[2]
    month = time.split(' ')[3]
    year = time.split(' ' )[4]
    detail_time = time.split(' ')[5]
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
    return year + '-' + month + '-' + day + ' ' + detail_time

class the_first_web(scrapy.Spider):
    name = 'the_first'
    website_id = 1137  # 网站的id(必填)
    language_id =  1930 # 所用语言的id
    start_urls = ['https://www.inextlive.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_cxq',
        'password': 'dg_cxq',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(the_first_web, self).__init__(*args, **kwargs)
        self.time = time

    def parse(self, response, **kwargs):
        html = BeautifulSoup(response.text)
        parese_url = html.select('#mainNav > ul > li')

        #只用爬取 2—13 的网站
        for i in range(0 , 14):
            if i >= 2 :
                #把每个栏目的url送到二级目录中
                yield Request(parese_url[i].a['href'], callback=self.parse_1)

    def parse_1(self , response):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36 Edg/80.0.361.61'
        }
        news_list = []
        soup = BeautifulSoup(response.text , 'lxml')
        #爬取二级目录下面的每个新闻，包括翻页！！！
        if len(soup.select('.topicList > li')):
            for new in soup.select('.topicList > li'):
                try:
                    if new.a['href']:
                        news_list.append(new.a['href'])
                        yield Request(new.a['href'] , callback=self.parse_2)
                except:
                    continue

        if len(soup.select('article li a')):
            for new in soup.select('article li a'):
                try:
                    news_list.append(new.a['href'])
                    yield Request(new.a['href'],  callback=self.parse_2)
                except:
                    continue
        #j决定爬取的页数
        j = 0
        while j < 5 and soup.select('.topicList > li'):
            next_page_url = soup.find('li', class_='last')
            try:
                soup = BeautifulSoup(requests.get(next_page_url, header).text, 'lxml')
                if len(soup.select('.topicList > li')):
                    for new in soup.select('.topicList > li'):
                        try:
                            if new.a['href']:
                                news_list.append(new.a['href'])
                                yield Request(new.a['href'], callback=self.parse_2)
                        except:
                            continue
                    # print("找不到具体新闻链接  1  " + parse1[i].a['href'])

                if len(soup.select('article li a')):
                    for new in soup.select('article li a'):
                        try:
                            news_list.append(new.a['href'])
                            yield Request(new.a['href'], callback=self.parse_2)
                        except:
                            continue
                j = j + 1
            except:
                break

    def parse_2(self, response, **kwargs):
        item = DemoItem()
        new_soup = BeautifulSoup(response.text, 'lxml')
        item['title'] = new_soup.find('div', class_='topHeading', id='12').h1.string

        bodys = new_soup.select('article .articleBody > p')
        #文章内容
        all_body = ''
        for body_1 in bodys:
            all_body += body_1.text
        item['body'] = all_body
        item['pub_time'] = time_font(new_soup.select('.articleHd .dateInfo .fl')[0].text).strip("\t")
        #图片url
        image_list = []
        if len(new_soup.find_all('img', id='jagran_image_id')):
            for image in new_soup.find_all('img', id='jagran_image_id'):
                image_list.append(
                    new_soup.find("body").select_one(".container .ls-area-body article .bodySummery").find("img").get("data-src"))
        item['images'] = image_list
        item['category1'] = new_soup.select('aside.breadcrum li.first > a > span')[0].string
        item['category2'] = new_soup.select('aside.breadcrum li:nth-of-type(3) > a > span')[0].text
        item['abstract'] = new_soup.select('aside.breadcrum li:nth-of-type(4) > span')[0].text
        yield item

