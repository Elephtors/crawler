import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time


class ZeenSpider(scrapy.Spider):
    name = 'zeenews'
    allowed_domains = ['zeenews.india.com']
    start_urls = ['https://zeenews.india.com/hindi']
    website_id = 1033  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    hindi_month = {
        'जनवरी': 'Jan',
        'फ़रवरी': 'Feb',
        'जुलूस': 'Mar',
        'अप्रैल': 'Apr',
        'मई': 'May',
        'जून': 'Jun',
        'जुलाई': 'Jul',
        'अगस्त': 'Aug',
        'सितंबर': 'Sept',
        'अक्टूबर': 'Oct',
        'नवंबर': 'Nov',
        'दिसंबर': 'Dec'
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(ZeenSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in soup.select('li.channel a'):
            meta = {'category1': i.text, 'category2': None, 'title': None, 'abstract': None, 'images': None}
            url = ('https://zeenews.india.com' + i.get('href'))
            if url.split('/')[-1] not in ['entertainment', 'elections', 'astro']:
                yield Request(url,callback=self.parse_eassys, meta=meta)

    def parse_eassys(self, response):  # 各类二级目录的文章的翻页和url爬取
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = True
        if re.match(r'.*photo-gallery.*', response.url):  # 照片的
            for t in soup.find_all(class_='col-sm-4 col-md-4 photo-photo-h'):
                try:
                    url = 'https://zeenews.india.com' + t.select_one('a').get('href')
                except:
                    continue
                response.meta['title'] = t.select_one('h3').text
                response.meta['images'] = [t.select_one('img').get('src')]
                response.meta['pub_time'] = t.select_one('.photo-date').text.strip()
                if self.time is None or Util.format_time3(Util.format_time2(t.select_one('.photo-date').text.strip())) >= int(self.time):
                    yield Request(url, callback=self.parse_item_photo, meta=response.meta)
                else:
                    flag = False
                    self.logger.info('时间截止')
                    break
        elif re.match(r'.*video.*', response.url):  # 视频的
            for i in soup.find_all(attrs={'class': 'mini-video mini-video-h margin-bt30px'}):  # 该目录初始的文章
                url = 'https://zeenews.india.com' + i.select_one('a').get('href')
                #self.logger.info( url)
                response.meta['images'] = [i.select_one('img').get('src')]
                response.meta['title'] = i.select_one('h3').text
                response.meta['pub_time'] = i.select_one('.date').text.strip()
                if self.time is None or Util.format_time3(Util.format_time2(i.select_one('span.date').text.strip())) >= int(self.time):
                    yield Request(url, callback=self.parse_item_video, meta=response.meta)
                else:
                    flag = False
                    self.logger.info('时间截止')
                    break
        else:
            for t in soup.find_all(class_='section-article margin-bt30px clearfix'):  # 该目录初始的文章
                url = 'https://zeenews.india.com' + t.select_one('a').get('href')
                response.meta['title'] = t.select_one('h3.margin-bt10px').text
                tt = t.select_one('span.date').text.strip().split()
                try:
                    pub_time = self.hindi_month[tt[0]] +' '+tt[1]+' '+tt[2]+' '+tt[3]+' '+tt[5]
                except:
                    pub_time = t.select_one('span.date').text.strip()
                response.meta['pub_time'] = pub_time
                response.meta['images'] = [t.select_one('img').get('src')]
                if self.time is None or Util.format_time3(Util.format_time2(pub_time)) >= int(self.time):
                    yield Request(url=url, meta=response.meta, callback=self.parse_item)
                else:
                    flag = False
                    self.logger.info('时间截止')
                    break
        if flag:
            try:
                nextPage = 'https://zeenews.india.com/'+ soup.find(class_='next last').select_one('a').get('href')
                yield Request(nextPage,callback=self.parse_eassys,meta=response.meta)
            except:
                self.logger.info('Next page no more!')
    # 包含所需爬取字段的页面有三类：以图片呈现的、视频呈现、图文呈现的。 （，对于以视频呈现的，还不会爬视频，也不用爬视频，我爬视频页面的字符串字段。）
    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = response.meta['title'] if response.meta['title'] else soup.select_one('.article-heading').text
        #strtt = soup.find_all(class_='write-block margin-bt20px')[-1].text  # strtt 形如 'Jan 5, 2021, 02:51 PM IST'
        item['pub_time'] = Util.format_time2(response.meta['pub_time'])
        item['images'] = response.meta['images'] if response.meta['images'] else [
            soup.select_one('.img-responsive').get('src')]
        ss = ''
        for p in soup.select('.field-items')[1]:
            ss += p.text + '\n'
        item['body'] = ss
        item['abstract'] = response.meta['abstract'] if response.meta['abstract'] is not None else soup.select_one('.margin-bt10px').text
        return item

    def parse_item_photo(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = response.meta['title']
        item['pub_time'] = Util.format_time2(response.meta['pub_time'])
        item['images'] = [i.get('src') for i in soup.select('.main-photo-block img')].append(response.meta['images'][0])
        item['body'] = soup.select_one('p.margin-bt10px').text
        item['abstract'] = soup.select_one('p.margin-bt10px').text
        return item

    def parse_item_video(self, response):
        soup = BeautifulSoup(response.text,'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = response.meta['title']
        item['pub_time'] = Util.format_time2(response.meta['pub_time'])
        item['images'] = response.meta['images']
        item['body'] = soup.select_one('p.margin-bt10px').text
        item['abstract'] = soup.select_one('p.margin-bt10px').text
        return item
