'''
此网站为静态网址且无翻页
'''
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re
import time

#将爬虫类名和name字段改成对应的网站名
class tourismSpider(scrapy.Spider):# zdx
    name = 'tourism'
    website_id = 1219 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['http://www.tourism.gov.ph/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(tourismSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = soup.select("h4.media-heading>a")
        for news in news_list:
            url = "http://www.tourism.gov.ph" + news.get("href") if news.get("href") else None
            if url:
                yield scrapy.Request(url, callback=self.parse_news)

    def parse_news(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        # 发布时间
        pub_time_list = re.split(" |,", soup.select_one("h2.page-header>small").text) if soup.select_one("h2.page-header>small") else None
        time2 = Util.format_time()
        if pub_time_list:
            if pub_time_list[-4] == "January":
                time2 = pub_time_list[-1] + "-01-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "February":
                time2 = pub_time_list[-1] + "-02-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "March":
                time2 = pub_time_list[-1] + "-03-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "April":
                time2 = pub_time_list[-1] + "-04-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "May":
                time2 = pub_time_list[-1] + "-05-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "June":
                time2 = pub_time_list[-1] + "-06-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "July":
                time2 = pub_time_list[-1] + "-07-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "August":
                time2 = pub_time_list[-1] + "-08-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "September":
                time2 = pub_time_list[-1] + "-09-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "October":
                time2 = pub_time_list[-1] + "-10-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "November":
                time2 = pub_time_list[-1] + "-11-" + pub_time_list[-3] + " 00:00:00"
            elif pub_time_list[-4] == "December":
                time2 = pub_time_list[-1] + "-12-" + pub_time_list[-3] + " 00:00:00"
        pub_time = time2
        # 标题
        temp = soup.select_one("h2.page-header")
        [s.extract() for s in temp('small')]
        title = temp.text.strip()
        # 正文
        body_list2 = []
        body_list = re.split("\r\n|\n", soup.select_one("div.col-md-12>p").text.strip())
        for b in body_list:
            if b:
                body_list2.append(b)
        body = "\n".join(body_list2)
        # 摘要
        abstract = body_list2[0]
        # 图片
        images = []
        temp_list = soup.select("center>img")
        for t in temp_list:
            images.append("http://www.tourism.gov.ph" + t.get("src"))

        item = DemoItem()
        item["category1"] = "News Updates"
        item["category2"] = "Featured News"
        item["pub_time"] = pub_time
        item["title"] = title
        item["abstract"] = abstract
        item["body"] = body
        item["images"] = images

        yield item