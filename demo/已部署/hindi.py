import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time

def translate_all(when):
    list = re.split(' |,|:', when)

    month = list[0]
    day = translate(list[1][0]) * 10 + translate(list[1][1])
    year = translate(list[3][0]) * 1000 + translate(list[3][1]) * 100 + translate(list[3][2]) * 10 + translate(
        list[3][3])
    hour = translate(list[4][0]) * 10 + translate(list[4][1])
    minute = translate(list[5][0]) * 10 + translate(list[5][1])
    all_time = str(month) + ' ' + str(day) + ' ' + str(year) + ' ' + str(hour) + ' ' + str(minute)
    return all_time

def translate(s):
    '''

    :param s: 印地语字符串
    :return: 字符串所对应的阿拉伯数字
    '''
    num=0
    if s == '०':
        num = 0
    elif s == '१':
        num = 1
    elif s == '२':
        num = 2
    elif s == '३':
        num = 3
    elif s == '४':
        num = 4
    elif s == '५':
        num = 5
    elif s == '६':
        num = 6
    elif s == '७':
        num = 7
    elif s == '८':
        num = 8
    elif s == '९':
        num = 9
    return num

class hindi(scrapy.Spider):
    name = 'hindi'
    website_id =  1071 # 网站的id(必填)
    language_id = 1930  # 所用语言的id
    # i = 1
    allowed_domains = ['parstoday.com']#一点开就变成这个网址
    start_urls = ['https://parstoday.com/hi']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(hindi, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()
        soup = bs(response.text, "html.parser")

        a_list = soup.find("div", class_="col-xs-12").select("li>a")
        # 如果有二级目录的话再另外处理
        for a in a_list[:-1]:
            category1_url = a.get("href")
            item['category1'] = a.text
            item['category2'] = None
            yield scrapy.Request(category1_url, callback=self.get_next_page, meta={"item": item,'category1_url':category1_url})  # 层与层之间通过meta参数传递数据
    def get_next_page(self, response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]
            # category1_url = response.meta["category1_url"]
            # print("现在的一级目录链接是"+category1_url)
            a_list = soup.find_all("a", class_="img")
            for a in a_list:
                article_url = a.get("href")
                yield scrapy.Request(article_url, callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据
            when = soup.find("div", class_="date").text

            if self.time == None or Util.format_time3(Util.format_time2(translate_all(when))) >= int(self.time):
                  if soup.find("a",class_="btn btn-default"):
                    url = soup.find("a",class_="btn btn-default").get("href")
                    yield scrapy.Request(url, callback=self.get_next_page, meta={"item": item})
            else:
                self.logger.info('时间截止')

    def get_news_detail(self,response):
        '''
        :param response: x新闻正文response
        :return: 新闻页面详情信息
        '''
        item = response.meta["item"]

        soup = bs(response.text, "html.parser")
        title = soup.find("h2", class_="item-title").text.strip() if soup.find("h2", class_="item-title") else None
        pub_time = translate_all(soup.find("div", class_="item-date").text.rsplit(" ", 1)[0]) if soup.select_one("div",
                                                                                                                 class_="item-date") else None
        # print(soup.find("div",class_="item-date").text)
        # image_list = [figure.select_one("img").get("src") if figure.select_one("img") else None for figure in soup.find_all("figure",class_="img")] if  soup.find("figure",class_="img") else None
        # 文章标题下的图片
        image_list = [li.select_one("figure>img").get("src") if li.select_one("figure>img") else '' for li in
                      soup.find_all("li", class_="photo")]
        # 文章中间的图片
        text_img = soup.select("#item > div > div.item-body > div.row > div > div.item-text > figure > img")
        for img in text_img:
            image_list.append(img.get("src"))
        abstract = soup.find("p", class_="introtext").text  # 正文第一句话为摘要
        body = ''
        for p in soup.select("#item > div > div.item-body > div.row > div > div.item-text > p")[1:]:
            body += (p.text + '\n')
        item["title"] = title.strip()
        item["pub_time"] = Util.format_time2(pub_time)
        item["images"] = image_list
        item["abstract"] = abstract.strip()
        item["body"] = body
        yield item
