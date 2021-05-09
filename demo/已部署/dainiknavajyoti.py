
# 此文件包含的头文件不要修改
import requests
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time
from datetime import datetime
import socket

#将爬虫类名和name字段改成对应的网站名
class dainiknavajyotiSpider(scrapy.Spider):
    name = 'dainiknavajyoti'
    website_id = 1002 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['http://www.dainiknavajyoti.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(dainiknavajyotiSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select('ul#topbar li a') if soup.select('ul#topbar li a') else None
        del categories[0], categories[-1], categories[-3], categories[-1]
        for category in categories:
            category_hrefList.append("https://www.dainiknavajyoti.net" + category.get('href'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        socket.setdefaulttimeout(30)
        soup = BeautifulSoup(response.text, features="lxml")

        article_hrefs = []
        articles = soup.select('div.section_news h3 a') if soup.select('div.section_news h3 a') else None
        for href in articles:
            if href.get('href') == "https://www.dainiknavajyoti.net/editorial/Know-what-is-special-in-the-government.html":
                continue
            else:
                article_hrefs.append(href.get('href'))
        for detail_url in article_hrefs:
            yield Request(detail_url, callback=self.parse_detail)



        # print(article_hrefs[-1] + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        check_soup = BeautifulSoup(requests.get(article_hrefs[-1]).content, features="lxml")
        temp_time = check_soup.select_one('div.pubdate').text.strip() if check_soup.select_one('div.pubdate').text.strip() else None
        adjusted_time = time_adjustment(temp_time)
        if self.time is None or Util.format_time3(adjusted_time) >= int(self.time):
            nav_li = soup.select('ul#pagination li') if soup.select('ul#pagination li') else None
            for li in nav_li:
                if li.text == "Next»":
                    yield Request(li.select_one('a').get('href'), callback=self.parse_category)
        else:
            self.logger.info("时间截止")




    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['pub_time'] = time_adjustment(soup.select_one('div.pubdate').text.strip() if soup.select_one('div.pubdate').text.strip() else None)
        image_list = []
        imgs = soup.select('img.adjimage1') if soup.select('img.adjimage1') else None
        if imgs:
            for img in imgs:
                image_list.append("https://www.dainiknavajyoti.net/" + img.get('src'))
            item['images'] = image_list
        p_list = []
        all_p = soup.select('div#contentsec p') if soup.select('div#contentsec p') else None
        for paragraph in all_p:
            p_list.append(paragraph.text)
        body = '\n'.join(p_list)
        item['abstract'] = p_list[0]
        item['body'] = body
        item['category1'] = soup.select_one('div[style="font-size:28px;padding-bottom:0px;"]').text.strip() if soup.select_one('div[style="font-size:28px;padding-bottom:0px;"]').text.strip() else None
        item['title'] = soup.find('div', class_="col-xs-12 col-md-8").select_one('div h3').text if soup.find('div', class_="col-xs-12 col-md-8").select_one('div h3').text else None
        yield item



def time_adjustment(input_time):
    time_elements = input_time.split(", ")
    get_month_day = time_elements[1].split(" ")
    get_year_time = time_elements[2].split(" ")
    # month = {
    #     'जनवरी': '01',
    #     'फ़रवरी': '02',
    #     'जुलूस': '03',
    #     'अप्रैल': '04',
    #     'मई': '05',
    #     'जून': '06',
    #     'जुलाई': '07',
    #     'अगस्त': '08',
    #     'सितंबर': '09',
    #     'अक्टूबर': '10',
    #     'नवंबर': '11',
    #     'दिसंबर': '12'
    # }
    month = {
        'January': '01',
        'February': '02',
        'March': '03',
        'April': '04',
        'May': '05',
        'June': '06',
        'July': '07',
        'August': '08',
        'September': '09',
        'October': '10',
        'November': '11',
        'December': '12'
    }
    # month = {
    #     'Jan': '01',
    #     'Feb': '02',
    #     'Mar': '03',
    #     'Apr': '04',
    #     'May': '05',
    #     'Jun': '06',
    #     'Jul': '07',
    #     'Aug': '08',
    #     'Sep': '09',
    #     'Oct': '10',
    #     'Nov': '11',
    #     'Dec': '12'
    # }
    return "%s-%s-%s %s:%s" % (get_year_time[0], month[get_month_day[0]], get_month_day[1], get_year_time[1], "00")


