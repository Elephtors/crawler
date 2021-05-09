import scrapy
from demo.items import DemoItem
from demo.util import Util
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re

class HatawtabloidSpider(scrapy.Spider):
    name = 'hatawtabloid'
    website_id = 532  # 网站的id(必填)
    language_id = 2117  # 所用语言的id
    allowed_domains = ['hatawtabloid.com']
    start_urls = ['https://www.hatawtabloid.com/category/news/',
                  'https://www.hatawtabloid.com/category/opinion/',
                  'https://www.hatawtabloid.com/category/bulabugin/',
                  'https://www.hatawtabloid.com/category/showbiz/',
                  'https://www.hatawtabloid.com/category/sports/',
                  'https://www.hatawtabloid.com/category/hataw-lifestyle/',
                  'https://www.hatawtabloid.com/category/greetings/',
                  'https://www.hatawtabloid.com/category/events/']
    sql = {  # sql配置
            'host': '127.0.0.1',#新的
            'user': 'root',
            'password': 'asdfghjkl',
            'db': 'dg_test'
        }

    cookie = '__cfduid=dc2df189dc00ca57cd9ac4bc0c54f945b1612168960; _ga=GA1.3.230726060.1612170596; _gid=GA1.3.1540972717.1612170596; __gads=ID=08329c20077c67e8-22d22bb7e4c500d1:T=1612170595:RT=1612170595:S=ALNI_MYa_4tLJuwwvw9yrbHbi8FAfOKVZw; _gat=1; cf_clearance=ae97d766b588be28c400f968e7e52d40636c5274-1612173019-0-150; PHPSESSID=85b3b46e408c6d994742a4eca5468b9c'
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'

    def __init__(self, time=None, *args, **kwargs):
        super(HatawtabloidSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def start_requests(self):
        for i in self.start_urls:
            yield Request(i,meta={'page':1,'url':i, 'User-Agent':self.ua, 'Cookie':self.cookie})

    def parse(self,response):
        soup = bs(response.text)
        flag = True
        for i in soup.select('.post-listing article'):
            if self.time == None or Util.format_time3(Util.format_time2(i.select('.post-meta')[0].text)) >= int(self.time):
                yield Request(i.select('h2 a')[0].attrs['href'], callback=self.parse_news, meta=response.meta)
            else:
                flag = False
                self.logger.info("时间截止")
                break
        if flag:
            response.meta['page']+=1
            yield Request(response.meta['url']+'/page/'+str(response.meta['page']), meta=response.meta)

    def parse_news(self,response):
        soup = bs(response.text)
        item = DemoItem()
        item["pub_time"] = Util.format_time2(soup.select('.post-meta > span')[1].text)
        title = soup.find("h1",class_="post-title entry-title").text.strip() if soup.find("h1",class_="post-title entry-title") else None
        item["title"] = title
        image = [soup.find("div",class_="single-post-thumb").find("img").get("src")] if soup.find("div",class_="single-post-thumb") else None
        item["images"] = image
        category1 = soup.select_one("#main-content > div > article > div > p > span:nth-child(3) > a").text.strip()
        item["category1"] = category1
        item["category2"] = None
        abstract = soup.find("div",class_="entry").find("p").text.strip() if soup.find("div",class_="entry") else soup.find("div",class_="entry").find("p").text.strip()
        item["abstract"] = abstract
        body = [p.text.strip() for p in soup.find("div",class_="entry").find_all("p")] if soup.find("div",class_="entry") else None
        body = "\n".join(body)
        item["body"] = body
        yield item