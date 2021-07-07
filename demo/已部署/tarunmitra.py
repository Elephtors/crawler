import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
import time
from datetime import datetime
import re

def format_time2(s):
    '''

    :param s:原时间格式为November 24, 2020- 9:42 AM
    :return: 返回2020-11-24 9:42:00
    '''
    pub_time = re.split(" |,|:|-", s)
    year = pub_time[3]
    month = pub_time[0]
    month = month.strip()
    if month == "January":
        month = 1
    elif month == "February":
        month = 2
    elif month == "March":
        month = 3
    elif month == "April":
        month = 4
    elif month == "May":
        month = 5
    elif month == "June":
        month = 6
    elif month == "July":
        month = 7
    elif month == "August":
        month = 8
    elif month == "September":
        month = 9
    elif month == "October":
        month = 10
    elif month == "November":
        month = 11
    elif month == "December":
        month = 12
    day = pub_time[1]
    hour = pub_time[5] if pub_time[-1] == 'AM' else int(pub_time[5]) + 12
    if hour == 24:
        hour = 12
    minute = pub_time[-2]
    # pub_time= "%s-%s-%s %s:%s:00" % (year, month, day, hour, minute)
    # return pub_time
    return time.strftime("%Y-%m-%d %H:%M:%S", datetime(int(year), month, int(day), int(hour), int(minute)).timetuple())

def format_time3(data):
    # 根据指定的格式把一个时间字符串解析为时间元组
    timeArray = time.strptime(data, "%Y-%m-%d %H:%M:%S")  # 转化为元组
    timeStamp = int(time.mktime(timeArray))  # 变成秒，参数必须是元组
    return timeStamp

class tarunmitraSpider(scrapy.Spider):
    name = 'tarunmitra'
    website_id =  1112 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['tarunmitra.in']
    start_urls = ['https://tarunmitra.in/']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(tarunmitraSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()
        soup = bs(response.text, "html.parser")

        ul = soup.select_one("#menu-main-menu")
        li_list = ul.select("li")
        for li in li_list[2:-4]:
            category1_url = li.select_one("a").get("href")
            # item['category1_url'] =  category1_url
            category = li.select_one("a").text
            item['category2'] = ''
            if ':' in category:
                # print("这个有二级目录")
                item['category1'] = category.split(":")[0]
                #有二级目录就先进入一级目录再去得到二级目录链接
                yield scrapy.Request(category1_url, callback=self.get_category2,meta={"item": item})  # 层与层之间通过meta参数传递数据
            else:
                item['category1'] = category
                yield scrapy.Request(category1_url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据
    def get_category2(self,response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]

            p_list = soup.find("div", class_="entry").select("p>strong>a")
            for a in p_list:
                category2_url = a.get("href")
                item['category2'] = a.text.strip()
                yield scrapy.Request(category2_url, callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据
    def get_next_page(self, response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]
            article_list = soup.find_all("article", class_="item-list")
            for article in article_list:
                    article_url = article.select_one("h2>a").get("href")

                    yield scrapy.Request(article_url, callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据

            if self.time == None or format_time3(format_time2(soup.select("#main-content > div.content > div > article > p > span")[-1].text)) >= int(self.time):
                url = soup.select_one("#tie-next-page > a").attrs['href'] if soup.select_one("#tie-next-page > a") else None
                if url:
                    yield scrapy.Request(url, meta=response.meta, callback=self.get_next_page)
            else:
                self.logger.info('时间截止')

    def get_news_detail(self,response):
        '''

        :param response: x新闻正文response
        :return: 新闻页面详情信息
        '''
        item = response.meta["item"]

        soup = bs(response.text, "html.parser")
        title = soup.find("h1", class_="name post-title entry-title").text if soup.find("h1",
                                                                                class_="name post-title entry-title") else None
        pub_time = soup.find("span", class_="tie-date").text if soup.find("span", class_="tie-date") else None

        image_list = [img.get("src") for img in soup.find_all("img", class_="attachment-full size-full wp-post-image")] if soup.find_all("img",class_="attachment-full size-full wp-post-image") else None

        abstract = soup.select_one("#the-post > div > div.entry >p").text.strip() if soup.select_one("#the-post > div > div.entry >p") else None
        # body = "\n".join([p.text.strip() for p in soup.select("#the-post > div > div.entry >p")] if soup.select("#the-post > div > div.entry >p") else None)
        body = ''
        for p in soup.select("#the-post > div > div.entry >p"):
            body += (p.text + '\n')
        item["title"] = title
        item["pub_time"] = format_time2(pub_time)
        item["images"]=image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item
