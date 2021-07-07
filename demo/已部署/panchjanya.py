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
class panchjanyaSpider(scrapy.Spider):
    name = 'panchjanya'
    website_id = 1007 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['https://www.panchjanya.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(panchjanyaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time
    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select('ul.parent_link li') if soup.select('ul.parent_link li') else None
        del categories[0]
        del categories[0]
        del categories[13:17]
        for category in categories:
            category_hrefList.append(category.select_one('a').get('href'))
            # category_nameList.append(category.text.replace('\n', ''))
        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)
    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category = soup.find('div', class_="box-shadow-block box-shadow-1 text-center").text if soup.find('div', class_="box-shadow-block box-shadow-1 text-center").text else None
        articles = list(soup.find_all('div', class_="col-md-6 col-sm-6 col-xs-12")) if soup.find_all('div', class_="col-md-6 col-sm-6 col-xs-12") else None
        article_hrefs = []
        for article in articles:
            if article.select_one('a').get('href') == "Nation.html":
                article_hrefs.append(article.select('a')[-1].get('href'))
            else:
                article_hrefs.append(article.select_one('a').get('href'))
        for detail_url in article_hrefs:
            yield Request(detail_url, callback=self.parse_detail, meta={'category': category})
    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['category1'] = response.meta['category']
        item['title'] = soup.select_one('div.heading_container').text if soup.select_one('div.heading_container') else soup.select_one('.heading.clsNewsTitleHeading1').text
        p_list = []
        if soup.select('div.newscontent p'):
            all_p = soup.select('div.newscontent p')
        else:
            all_p = soup.select('div[align="justify"]')
        for paragraph in all_p:
            p_list.append(paragraph.text)
        body = '\n'.join(p_list)
        if len(p_list):
            item['abstract'] = p_list[0]
        item['body'] = body
        image_list = []
        imgs = soup.select('div[align="center"] img') if soup.select('div[align="center"] img') else None
        if imgs:
            for img in imgs:
                image_list.append(img.get('src'))
            item['images'] = image_list
        if soup.select_one('div.date_and_author_container span'):
            temp_time = soup.select_one('div.date_and_author_container span').text.split(" ")[1]
        else:
            temp_time = soup.select_one('td.miscinfo').text.split(" ")[1]
        try:
            item['pub_time'] = time_adjustment(temp_time)
        except Exception:
            item['pub_time'] = Util.format_time()
        yield item
def time_adjustment(input_time):
    time_elements = input_time.split("-")
    # print(time_elements[1]+"$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    if time_elements[1] == "जनवरी" or time_elements[1] == "à¤à¤¨à¤µà¤°à¥":
        month = "01"
    elif time_elements[1] == "फ़रवरी" or time_elements[1] == "à¤«à¤¼à¤°à¤µà¤°à¥":
        month = "02"
    elif time_elements[1] == "जुलूस" or time_elements[1] == "à¤®à¤¾à¤°à¥à¤":
        month = "03"
    elif time_elements[1] == "अप्रैल" or time_elements[1] == "à¤à¤ªà¥à¤°à¥à¤²":
        month = "04"
    elif time_elements[1] == "मई" or time_elements[1] == "à¤®à¤":
        month = "05"
    elif time_elements[1] == "जून" or time_elements[1] == "à¤à¥à¤¨":
        month = "06"
    elif time_elements[1] == "जुलाई" or time_elements[1] == "à¤à¥à¤²à¤¾à¤":
        month = "07"
    elif time_elements[1] == "अगस्त" or time_elements[1] == "à¤à¤à¤¸à¥à¤¤":
        month = "08"
    elif time_elements[1] == "सितंबर" or time_elements[1] == "à¤¸à¤¿à¤¤à¤à¤¬à¤°":
        month = "09"
    elif time_elements[1] == "अक्टूबर" or time_elements[1] == "à¤à¤à¥à¤¤à¥à¤¬à¤°" or time_elements[1] == "अक्तूबर":
        month = "10"
    elif time_elements[1] == "दिसंबर" or time_elements[1] == "à¤¨à¤µà¤à¤¬à¤°":
        month = "11"
    elif time_elements[1] == "दिसंबर" or time_elements[1] == "à¤¦à¤¿à¤¸à¤à¤¬à¤°":
        month = "12"
    else:
        month = "None"
    return "%s-%s-%s" % (time_elements[2], month, time_elements[0]) + " 00:00:00"