
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

#将爬虫类名和name字段改成对应的网站名
class diariutimorpostSpider(scrapy.Spider):
    name = 'diariutimorpost'
    website_id = 690 # 网站的id(必填)
    language_id = 2122  # 所用语言的id
    start_urls = ['http://diariutimorpost.com/pt/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_lhl',
        'password': 'dg_lhl',
        'db': 'dg_test'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(diariutimorpostSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select("div#headerNav ul#menu-main-menu li a") if soup.select("div#headerNav ul#menu-main-menu li a") else None
        del categories[0]
        for category in categories:
            category_hrefList.append(category.get('href'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")

        article_hrefs = []
        articles = soup.select('div.title h3.h4 a') if soup.select('div.title h3.h4 a') else None
        if articles:
            meta = {
                "category1": soup.select_one('div.post--items-title h2.h4').text.split("Category: ")[1]
            }
            temp_time = soup.select('div.post--info ul li')[-1].text if soup.select('div.post--info ul li')[-1].text else None
            adjusted_time = time_adjustment(temp_time)
            if self.time is None or Util.format_time3(adjusted_time) >= int(self.time):
                for href in articles:
                    article_hrefs.append(href.get('href'))
                for detail_url in article_hrefs:
                    yield Request(detail_url, callback=self.parse_detail, meta=meta)
            else:
                self.logger.info("时间截止")




    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['pub_time'] = time_adjustment(soup.select('div.post--info ul li')[-1].text if soup.select('div.post--info ul li')[-1].text else None)
        image_list = []
        imgs = soup.select('div.post--img a img') if soup.select('div.post--img a img') else None
        if imgs:
            for img in imgs:
                image_list.append(img.get('src'))
            item['images'] = image_list
        p_list = []
        if soup.select('div.post--content h4'):
            all_p = soup.select('div.post--content h4')
            for paragraph in all_p:
                p_list.append(paragraph.text)
            body = '\n'.join(p_list)
            item['abstract'] = p_list[0]
            item['body'] = body

        item['category1'] = Response.meta["category1"]
        item['title'] = soup.select_one('div.title h2.titlePostDetail').text if soup.select_one('div.title h2.titlePostDetail').text else None
        yield item



def time_adjustment(input_time):
    time_elements = input_time.split(", ")
    get_month_day = time_elements[0].split(" ")
    year = time_elements[1]

    if int(get_month_day[1]) < 10:
        day = "0" + get_month_day[1]
    else:
        day = get_month_day[1]


    # month = {     # 印地语
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
    # month = {       # 葡萄牙语
    #     'janeiro': '01',
    #     'fevereiro': '02',
    #     'março': '03',
    #     'abril': '04',
    #     'maio': '05',
    #     'junho': '06',
    #     'julho': '07',
    #     'agosto': '08',
    #     'setembro': '09',
    #     'outubro': '10',
    #     'novembro': '11',
    #     'dezembro': '12'
    # }
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
    # if time_elements2[3] == "am":
    #     # return output_time.strip()[:-2]
    #     if get_hour_mins[0] == "12":
    #         return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], str(int(get_hour_mins[0]) - 12), get_hour_mins[1], "00")
    #     else:
    #         return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], get_hour_mins[0], get_hour_mins[1], "00")
    # else:
    #     if get_hour_mins[0] == "12":
    #         return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], get_hour_mins[0], get_hour_mins[1], "00")
    #     else:
    #         return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], str(int(get_hour_mins[0]) + 12),get_hour_mins[1], "00")

    return "%s-%s-%s %s:%s:%s" % (year, month[get_month_day[0]], day, "00", "00", "00")
