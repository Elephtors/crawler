from urllib.parse import urljoin
import re
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response

#将爬虫类名和name字段改成对应的网站名
class jbSpider(scrapy.Spider):
    name = 'jb'
    website_id = 678 # 网站的id(必填)
    language_id = 2122 # 所用语言的id
    start_urls = ['https://www.jb.com.br/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(jbSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        url = "https://www.jb.com.br/index.php?id=/"
        soup = BeautifulSoup(response.text, "html.parser")
        a_list = soup.select("div.css-1llhclm>ul.css-1vxc2sl>li.css-cwdrld>a.css-1wjnrbv")
        for a in a_list[1:]:
            meta["category1"] = a.text.strip()
            meta["category2"] = None
            meta["url"] = urljoin(url, a.get("href")) + "/index.php&p="
            meta["page_num"] = 1
            category_url = meta["url"] + str(meta["page_num"])
            yield scrapy.Request(category_url, meta=meta, callback=self.parse_news_list)

    def parse_news_list(self, response):
        url = "https://www.jb.com.br/"
        soup = BeautifulSoup(response.text, "html.parser")
        # 获取新闻列表
        temp = soup.find("ol", {"aria-live": "polite"})
        a_list = temp.select("li.css-ye6x8s>article.css-1cp3ece>div.css-1l4spti>a")
        for a in a_list:
            news_url = urljoin(url, a.get("href"))
            yield scrapy.Request(news_url, meta=response.meta, callback=self.parse_news)
        # 最后一条新闻取时间
        final_url = urljoin(url, a_list[-1].get("href")) if a_list else None
        if final_url:
            response.meta['dont_filter'] = True
            yield scrapy.Request(final_url, meta=response.meta, callback=self.parse_next_page, dont_filter=True)

    def parse_next_page(self, response):
        response.meta['dont_filter'] = False
        soup = BeautifulSoup(response.text, "html.parser")
        temp = soup.find("time", {"class": "css-1sbuyqj"}) if soup.find("time", {"class": "css-1sbuyqj"}) else None
        temp_text = temp.text.strip() if temp and temp.text else None
        time_list = re.split(",| ", temp_text) if temp_text else None
        time2 = ''
        if time_list:
            if time_list[3] == "Jan":
                time2 = time_list[5] + "-01-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Feb':
                time2 = time_list[5] + "-02-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Mar':
                time2 = time_list[5] + "-03-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Apr':
                time2 = time_list[5] + "-04-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'May':
                time2 = time_list[5] + "-05-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Jun':
                time2 = time_list[5] + "-06-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Jul':
                time2 = time_list[5] + "-07-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Aug':
                time2 = time_list[5] + "-08-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Sept':
                time2 = time_list[5] + "-09-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Oct':
                time2 = time_list[5] + "-10-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Nov':
                time2 = time_list[5] + "-11-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Dec':
                time2 = time_list[5] + "-12-" + time_list[1] + " " + time_list[6] + ":00"
        response.meta["page_num"] += 1
        next_page = response.meta["url"] + str(response.meta["page_num"])
        if self.time == None or (time2 and Util.format_time3(time2) >= int(self.time)):
            yield scrapy.Request(next_page, meta=response.meta, callback=self.parse_news_list)
        else:
            self.logger.info('时间截止')

    def parse_news(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, "html.parser")
        # 文章发布时间
        temp = soup.find("time", {"class": "css-1sbuyqj"}) if soup.find("time", {"class": "css-1sbuyqj"}) else None
        temp_text = temp.text.strip() if temp and temp.text else None
        time_list = re.split(",| ", temp_text) if temp_text else None
        time2 = Util.format_time()
        if time_list:
            if time_list[3] == "Jan":
                time2 = time_list[5] + "-01-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Feb':
                time2 = time_list[5] + "-02-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Mar':
                time2 = time_list[5] + "-03-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Apr':
                time2 = time_list[5] + "-04-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'May':
                time2 = time_list[5] + "-05-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Jun':
                time2 = time_list[5] + "-06-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Jul':
                time2 = time_list[5] + "-07-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Aug':
                time2 = time_list[5] + "-08-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Sept':
                time2 = time_list[5] + "-09-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Oct':
                time2 = time_list[5] + "-10-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Nov':
                time2 = time_list[5] + "-11-" + time_list[1] + " " + time_list[6] + ":00"
            elif time_list[3] == 'Dec':
                time2 = time_list[5] + "-12-" + time_list[1] + " " + time_list[6] + ":00"
        item["pub_time"] = time2
        # 文章图片
        images = []
        img = soup.select_one("picture>img").get("src") if soup.select_one("picture>img") else None
        if img:
            images.append(img)
        item["images"] = images
        # 文章内容
        body = []
        p_list = soup.select("p.css-158dogj")
        for p in p_list:
            if p.text:
                body.append(p.text.strip())
        item['body'] = "\n".join(body) if body else None
        # 文章摘要
        abstract = soup.find("p", {"id": "article-summary"}).text.strip() if soup.find("p", {"id": "article-summary"}) else ''
        if abstract == '' or abstract == '.':
            abstract = body[0] if body else None
        item["abstract"] = abstract
        # 一级目录
        item["category1"] = response.meta["category1"]
        # 二级目录
        item["category2"] = response.meta["category2"]
        # 文章标题
        item["title"] = soup.find("h1", {"id": "link-1b44e840"}).text.strip() if soup.find("h1", {"id": "link-1b44e840"}) else None
        yield item

