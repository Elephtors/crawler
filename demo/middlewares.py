
from scrapy import signals
import pymysql
from scrapy.http import Request
from fake_useragent import UserAgent
from scrapy.exceptions import IgnoreRequest

header = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
}

class DemoSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_output(self, response, result, spider): 
        for i in result:
            if isinstance(i,Request):
                yield i
            else:
                i['request_url'] = response.request.url
                i['response_url'] = response.url
                i['website_id'] = spider.website_id
                i['language_id'] = spider.language_id
                if 'images' not in i or i['images'] == None:
                    i['images'] = []
                if 'html' not in i:
                    i['html'] = response.text
                yield i

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
        

class DemoDownloaderMiddleware:
    def __init__(self):
        self.db = None
        self.cur = None      
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider): 
        self.cur.execute('select request_url from news where request_url = %s',request.url)
        result = self.cur.fetchall()

        # 请求头配置
        if ('dont_filter' in request.meta and request.meta['dont_filter'] == True) or result == ():
            if 'User-Agent' in request.meta:
                request.headers['User-Agent'] = request.meta['User-Agent']
            else:
                request.headers['User-Agent'] = str(UserAgent().random)

            if 'Cookie' in request.meta:
                request.headers['Cookie'] = request.meta['Cookie']

            # request.meta['proxy'] = 'http://192.168.235.227:8888'
            return None
        else:
            spider.logger.info('filtered url')
            return IgnoreRequest

    def spider_opened(self, spider): 
        self.db = pymysql.connect(
            host=spider.sql['host'],
            user=spider.sql['user'],
            password=spider.sql['password'],
            db=spider.sql['db'],
        )
        self.cur = self.db.cursor()

