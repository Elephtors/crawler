

from urllib.parse import urljoin
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import re

#将爬虫类名和name字段改成对应的网站名
class dohSpider(scrapy.Spider):
    name = 'doh'
    website_id = 1218 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://doh.gov.ph/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(dohSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        meta = {}
        meta['category2'] = ''
        meta['pub_time'] = ''
        category = soup.find("li", {"id": "menu-1929-1"}).find("a")
        meta['category1'] = category.text.strip()
        url = "https://doh.gov.ph" + category.get("href")
        yield scrapy.Request(url, meta=meta, callback=self.parse_news_list)

    def parse_news_list(self, response):
        home_url = 'https://doh.gov.ph/'
        time2 = ''
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = soup.select("div.panel>div>div.view-content>div")
        # 新闻列表
        for news in news_list:
            # 发布日期和时间
            date = news.find("span", class_="field-content content-time").text.strip()
            dtime = " 00:00:00"
            # 日期
            pub_time_list = re.split(" |,", date) if date else None
            if pub_time_list:
                if pub_time_list[0] == "January":
                    time2 = pub_time_list[-1] + "-01-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "February":
                    time2 = pub_time_list[-1] + "-02-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "March":
                    time2 = pub_time_list[-1] + "-03-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "April":
                    time2 = pub_time_list[-1] + "-04-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "May":
                    time2 = pub_time_list[-1] + "-05-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "June":
                    time2 = pub_time_list[-1] + "-06-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "July":
                    time2 = pub_time_list[-1] + "-07-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "August":
                    time2 = pub_time_list[-1] + "-08-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "September":
                    time2 = pub_time_list[-1] + "-09-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "October":
                    time2 = pub_time_list[-1] + "-10-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "November":
                    time2 = pub_time_list[-1] + "-11-" + pub_time_list[1] + dtime
                elif pub_time_list[0] == "December":
                    time2 = pub_time_list[-1] + "-12-" + pub_time_list[1] + dtime
            response.meta['pub_time'] = time2
            #新闻列表
            url = urljoin(home_url, news.find("a").get("href"))
            yield scrapy.Request(url, meta=response.meta, callback=self.parse_news)
        # 翻页
        next_page = "https://doh.gov.ph/" + soup.select_one("li.pager-next>a").get("href") if soup.select_one("li.pager-next>a") else None
        if self.time == None or (time2 and Util.format_time3(time2) >= int(self.time)):
            if next_page:
                yield scrapy.Request(next_page, meta=response.meta, callback=self.parse_news_list)
        else:
            self.logger.info('time out')

    def parse_news(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        item = DemoItem()
        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        item["pub_time"] = response.meta["pub_time"] if response.meta["pub_time"] else Util.format_time()
        item['title'] = soup.find("h5", class_="page__title title").text.strip()
        # 图片
        images = []
        div_list = soup.find_all("div", class_="field-item even")
        if len(div_list) == 2:
            image = div_list[0].find("img").get("src") if div_list[0].find("img") else None
            if image:
                images.append(image)
        item["images"] = images
        # 新闻正文
        btext_list = []
        temp_list = div_list[-1].findAll({"p", "li", "div", "span"})
        if len(temp_list) == 1:
            btext = temp_list[0].text.strip()
        else:
            for temp2 in temp_list:
                if temp2 and temp2.text.strip() not in btext_list:
                    btext_list.append(temp2.text.strip())
            btext = '\n'.join(btext_list)
        body_list = []
        body_list2 = btext.split("\xa0")
        for b in body_list2:
            if b:
                body_list.append(b)
        body = ' '.join(body_list)
        item['abstract'] = body.split('.')[0] + '...'
        item['body'] = body
        yield item