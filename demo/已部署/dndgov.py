import re
from datetime import datetime
import time
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response

#author：詹婕妤

class DndGovSpider(scrapy.Spider):
    name = 'dndgov'
    website_id = 1269  # 网站的id(必填)
    language_id = 2117  # 所用语言的id
    allowed_domains = ['www.dnd.gov.ph']
    start_urls = ['https://www.dnd.gov.ph/PostCategories/Title/DND%20News?type=Category%20Gallery&page=1&take=12',
                  'https://www.dnd.gov.ph/PostCategories/Title/DND%20Secretaries?take=24&page=1&type=Category_Gallery&Year=0&Month=0',
                  'https://www.dnd.gov.ph/PostCategories/Title/Press%20Release?type=Category%20Gallery&page=1&take=12']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(DndGovSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    month = {
        'January': 1,
        'February': 2,
        'March': 3,
        'April': 4,
        'May': 5,
        'June': 6,
        'July': 7,
        'August': 8,
        'September': 9,
        'October': 10,
        'November': 11,
        'December': 12,
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sept': 9,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }

    def parse(self, response):
        soup = bs(response.text,'html.parser')
        category1 = soup.select_one('#auxilliarymenu > div').text.strip()
        page = soup.select('#renderbody > div > div.paginationdiv > a')[-1].text.strip()
        for p in range(1,int(page)+1):
            page_url = response.url.split('page=')[0] + 'page=' + str(p) + '&' + response.url.split('page=')[1].split('&')[-1]
            yield scrapy.Request(page_url,callback=self.news_list,meta={'category1':category1})

    def news_list(self,response):
        soup = bs(response.text,'html.parser')
        for i in soup.select('#renderbody > div > div.PostGallery > a'):
            url = 'https://www.dnd.gov.ph' + i.get('href')
            pub_time = i.find(class_='smalldate').text.strip()
            pub = re.findall(r'\w+',pub_time)
            pub_time = time.strftime("%Y-%m-%d %H:%M:%S",datetime(int(pub[-1]),self.month[pub[1]],int(pub[-2])).timetuple())
            response.meta['title'] = i.find(class_='gallery_Title').text.strip()
            response.meta['pub_time'] = pub_time
            if self.time == None or Util.format_time3(pub_time) >= int(self.time):
                # self.logger.info(url)
                yield Request(url, meta=response.meta,callback=self.news)
            else:
                self.logger.info('截止')
                continue
                # break

    def news(self,response):
        soup = bs(response.text,'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = None
        item['pub_time'] = response.meta['pub_time']
        item['title'] = response.meta['title']
        images = ['https://www.dnd.gov.ph' + img.get('src') for img in soup.find(class_='text-center featuredimage').find_all('img')] if soup.find(class_='text-center featuredimage') else []
        body = ''
        if soup.find(class_='postcontainer'):
            for i in soup.select('div.postcontainer > div > p'):
                if i.find('img'):
                    images.append('https://www.dnd.gov.ph' + i.find('img').get('src'))
                body += i.text.strip() + '\n'
        item['images'] = images
        item['body'] = body
        item['abstract'] = item['body'].split('\n')[0]
        self.logger.info(item)
        yield item