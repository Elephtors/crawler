
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
class bharatkhabarSpider(scrapy.Spider):
    name = 'bharatkhabar'
    website_id = 1011 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    start_urls = ['http://www.bharatkhabar.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }


    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(bharatkhabarSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time


    def parse(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        category_hrefList = []
        # category_nameList = []
        categories = soup.select("ul#main_menu li a") if soup.select("ul#main_menu li a") else None
        del categories[-1]
        for category in categories:
            category_hrefList.append(category.get('href'))
            # category_nameList.append(category.text.replace('\n', ''))

        for category in category_hrefList:
            yield scrapy.Request(category, callback=self.parse_category)

    def parse_category(self, response):
        soup = BeautifulSoup(response.text, features="lxml")

        article_hrefs = []
        articles = soup.select('div.post_header_title h5 a') if soup.select('div.post_header_title h5 a') else None
        if articles:
            for href in articles:
                article_hrefs.append(href.get('href'))
            for detail_url in article_hrefs:
                yield Request(detail_url, callback=self.parse_detail)



        # print(article_hrefs[-1] + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # check_soup = BeautifulSoup(requests.get(article_hrefs[-1]).content, features="lxml")
            temp_time = soup.select('span.post_info_date')[-1].text.strip() if soup.select('span.post_info_date')[-1].text.strip() else None
            adjusted_time = time_adjustment(temp_time)
            if self.time is None or Util.format_time3(adjusted_time) >= int(self.time):
                if soup.select_one('a.prev_button'):
                    yield Request(soup.select_one('a.prev_button').get('href'), callback=self.parse_category)
            else:
                self.logger.info("时间截止")




    def parse_detail(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, features='lxml')
        item['pub_time'] = time_adjustment(soup.select_one('span.post_info_date').text.strip() if soup.select_one('span.post_info_date').text.strip() else None)
        image_list = []
        imgs = soup.find('div', class_="post_img static").select('img') if soup.find('div', class_="post_img static").select('img') else None
        if imgs:
            for img in imgs:
                if re.findall(r'data:image/gif',img.get('src')) == []:
                    image_list.append(img.get('src'))
            item['images'] = image_list
        p_list = []
        if soup.find('div', class_="post_header single").select('p'):
            all_p = soup.find('div', class_="post_header single").select('p')
            for paragraph in all_p:
                p_list.append(paragraph.text)
            body = '\n'.join(p_list)
            item['abstract'] = p_list[0]
            item['body'] = body
        else:
            item['abstract'] = soup.find('div', class_="post_header single").select_one('h1').text if soup.find('div', class_="post_header single").select_one('h1').text else None
            item['body'] = soup.find('div', class_="post_header single").select('h2')[-1].text if soup.find('div', class_="post_header single").select('h2')[-1].text else None
        item['category1'] = soup.select_one('div.breadcrumb').select('a')[-1].text if soup.select_one('div.breadcrumb').select('a')[-1].text else None
        item['title'] = soup.select_one('div.post_header_title h1').text if soup.select_one('div.post_header_title h1').text else None
        yield item



def time_adjustment(input_time):
    input_time2 = input_time.replace('Posted On ', '')
    time_elements = input_time2.split(", ")
    time_elements2 = time_elements[1].split(" ")
    get_month_day = time_elements[0].split(" ")
    get_hour_mins = time_elements2[2].split(":")
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
    if time_elements2[3] == "am":
        # return output_time.strip()[:-2]
        if get_hour_mins[0] == "12":
            return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], str(int(get_hour_mins[0]) - 12), get_hour_mins[1], "00")
        else:
            return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], get_hour_mins[0], get_hour_mins[1], "00")
    else:
        if get_hour_mins[0] == "12":
            return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], get_hour_mins[0], get_hour_mins[1], "00")
        else:
            return "%s-%s-%s %s:%s:%s" % (time_elements2[0], month[get_month_day[0]], get_month_day[1], str(int(get_hour_mins[0]) + 12),get_hour_mins[1], "00")


