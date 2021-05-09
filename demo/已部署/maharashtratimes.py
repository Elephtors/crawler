import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
from datetime import datetime
import time

class maharashtratimesSpider(scrapy.Spider):
    name = 'maharashtratimes'
    website_id = 473  # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://maharashtratimes.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(maharashtratimesSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('#fixedMenu > .items > ul a'):
            yield Request(i.attrs['href'],callback=self.parse1)

    def parse1(self, response):
        html = BeautifulSoup(response.text)
        if len(html.select('#childrenContainer > div > a[data-tn="tn"]')):
            yield Request(response.url+'?curpg=1',callback=self.parse2,meta={'page':1,'url':response.url})
        else:
            for i in html.select('#childrenContainer > div > .row.undefined a.read_more'):
                yield Request(i.attrs['href'],callback=self.parse1)

    def parse2(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('#childrenContainer > div .row.undefined li .con_wrap > a')[:-1]:
            yield Request(i.attrs['href'],callback=self.parse_detail)
        # 这里在列表中挑选最后一篇文章并传给parse_page，并通过meta把对应的列表信息也传过去用于翻页，dont_filter防止文章被查重
        response.meta['dont_filter'] = True
        yield Request(html.select('#childrenContainer > div .row.undefined li .con_wrap > a')[-1].attrs['href'],callback=self.parse_page,meta=response.meta,dont_filter=True)

    def parse_page(self, response): # 用于判断是否截止
        html = BeautifulSoup(response.text)
        response.meta['dont_filter'] = False
        list = re.findall(r'\d+ \S+ \d+, \d+:\d+:\d+',html.select('.source .time')[0].text)[0].split(' ')
        timetext = time.strftime("%Y-%m-%d ", datetime(int(list[2].split(',')[0]),Util.month[list[1]],int(list[0])).timetuple())+list[3]
        if self.time == None or Util.format_time3(timetext) >= int(self.time):
            #这里使用的是传页数然后+1的做法，也可以用其他的方法实现，例如在上一层爬取了下一页的url后传过来
            response.meta['page'] += 1
            yield Request(response.meta['url']+'?curpg='+str(response.meta['page']),meta=response.meta,callback=self.parse2)
        else:
            self.logger.info('截止')
        #判断完就把文章传给parse_detail
        yield Request(response.url,callback=self.parse_detail)

    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text)
        item['title'] = soup.find("div", class_="story-article").find("h1").text if soup.find("div",
                                                                                              class_="story-article").find("h1") else None
        item['abstract'] = soup.find("div", class_="story-article").find("h2").text if soup.find("div",
                                                                                                 class_="story-article").find("h2") else None
        list = re.findall(r'\d+ \S+ \d+, \d+:\d+:\d+',soup.select('.source .time')[0].text)[0].split(' ')
        timetext = time.strftime("%Y-%m-%d ", datetime(int(list[2].split(',')[0]),Util.month[list[1]],int(list[0])).timetuple())+list[3]
        item['pub_time'] = timetext
        image_list = []
        image = soup.find("div", class_="img_wrap").find_all("img") if soup.find("div", class_="img_wrap") else None
        for img in image:
            image_list.append(img.get("src"))
        item['images'] = image_list
        body = soup.find("article")
        delete = [s.extract() for s in body("a") and body("strong")]
        item['body'] = body.text if soup.find("article") else None
        categorymenu = soup.find("div", class_="breadcrumb").find_all("li")[:2]
        item['category1'] = categorymenu[0].text if soup.find("div", class_="breadcrumb") else None
        item['category2'] = categorymenu[1].text if soup.find("div", class_="breadcrumb") else None

        yield item
