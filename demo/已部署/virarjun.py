
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime

#将爬虫类名和name字段改成对应的网站名
class virarjunSpider(scrapy.Spider):
    name = 'virarjun'
    website_id = 994 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['http://www.virarjun.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(virarjunSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select('ul.main-menu li') if soup.select('ul.main-menu li') else None
        categories.pop()
        categories.pop(0)
        for category in categories:
            category_hrefList.append("http://www.virarjun.com"+category.select_one('a').get('href'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")

        articles = soup.select('div.article-header h2 a')
        article_hrefs = []
        for article in articles:
            article_href = "http://www.virarjun.com" + article.get('href')
            article_hrefs.append(article_href)
        for detail_url in article_hrefs:
            yield Request(detail_url, callback=self.parse_detail)

        #时间截止
        time_list = soup.select('div.article-content span.convert-to-localtime')
        try:
            limited_time = datetime.strptime(time_list[-1].text, "%d %b %Y %I:%M %p GMT")
        except:
            limited_time = datetime.strptime(time_list[-1].text, "%d %B %Y %I:%M %p GMT")
        if self.time == None or Util.format_time3(str(limited_time)) >= int(self.time):
            #翻页
            if soup.select_one('div.page-pager a span.icon-text'):
                page_a = soup.select('div.page-pager a')
                for a in page_a:
                    if a.text == "Next  ":
                        yield Request(a.get('href'), callback=self.parse_category)
        else:
            self.logger.info("时间截止")


    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        temp_time = soup.select_one('span.convert-to-localtime') if soup.select_one('span.convert-to-localtime') else None
        try:
            item['pub_time'] = datetime.strptime(temp_time.text, "%d %b %Y %I:%M %p GMT")
        except:
            item['pub_time'] = datetime.strptime(temp_time.text, "%d %B %Y %I:%M %p GMT")
        image_list = []
        imgs = soup.select('h2 img') if soup.select('h2 img') else None
        if imgs:
            for img in imgs:
                image_list.append("http://www.virarjun.com/"+img.get('src'))
            item['images'] = image_list
        p_list = []
        all_p = soup.find('div', class_="details-content-story shortcode-content").select('p') if soup.find('div', class_="details-content-story shortcode-content").select('p') else None
        for p in all_p:
            if p.text == '' or p.text == ' ':
                all_p.remove(p)

        for paragraph in all_p:
            p_list.append(paragraph.text)
        body = '\n'.join(p_list)


        item['abstract'] = p_list[0]
        item['body'] = body
        item['category1'] = soup.select('div.tag-block a')[1].text + "\b\b\b" if soup.select('div.tag-block a')[1].text else None

        item['title'] = soup.select_one('h1.article-title').text if soup.select_one('h1.article-title').text else None
        yield item



# def time_adjustment(input_time):
#     get_year = input_time.split(", ")
#     month_day = get_year[0].split(" ")
#     if month_day[0] == "जनवरी":
#         month = "01"
#     elif month_day[0] == "फ़रवरी":
#         month = "02"
#     elif month_day[0] == "मार्च":
#         month = "03"
#     elif month_day[0] == "अप्रैल":
#         month = "04"
#     elif month_day[0] == "मई":
#         month = "05"
#     elif month_day[0] == "जून":
#         month = "06"
#     elif month_day[0] == "जुलाई":
#         month = "07"
#     elif month_day[0] == "अगस्त":
#         month = "08"
#     elif month_day[0] == "सितंबर":
#         month = "09"
#     elif month_day[0] == "अक्टूबर":
#         month = "10"
#     elif month_day[0] == "नवंबर":
#         month = "11"
#     elif month_day[0] == "दिसंबर":
#         month = "12"
#     else:
#         month = "None"
#
#     if int(month_day[1]) < 10:
#         day = "0" + month_day[1]
#     else:
#         day = month_day[1]
#
#     return "%s-%s-%s" % (get_year[1], month, day) + " 00:00:00"
