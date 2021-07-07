import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
import re
from datetime import datetime
import time

def format_time2(s):
    '''

    :param s:原时间格式为Tuesday, 22 Dec 2020 10:42:26 AM
    :return: 返回2020-12-22 10:42:26
    '''
    pub_time = re.split(" |,|:", s)
    # 同一个位子切两次就会有一个元素是''
    #切割完之后变这样['Tuesday', '', '22', 'Dec', '2020', '10', '42', '26', 'AM']
    year = pub_time[4]
    month = pub_time[3]
    month = month.strip()
    if month == "Jan":
        month = 1
    elif month == "Feb":
        month = 2
    elif month == "Mar":
        month = 3
    elif month == "Apr":
        month = 4
    elif month == "May":
        month = 5
    elif month == "Jun":
        month = 6
    elif month == "Jul":
        month = 7
    elif month == "Aug":
        month = 8
    elif month == "Sep":
        month = 9
    elif month == "Sept":
        month = 9
    elif month == "Oct":
        month = 10
    elif month == "Nov":
        month = 11
    elif month == "Dec":
        month = 12
    day = pub_time[2]
    hour = pub_time[5] if pub_time[-1] == 'AM' else int(pub_time[5]) + 12
    if hour == 24:
        hour = 12
    minute = pub_time[6]
    second = pub_time[7]

    return time.strftime("%Y-%m-%d %H:%M:%S", datetime(int(year), month, int(day), int(hour), int(minute),int(second)).timetuple())

def format_time3(data):
    # 根据指定的格式把一个时间字符串解析为时间元组
    timeArray = time.strptime(data, "%Y-%m-%d %H:%M:%S")  # 转化为元组
    timeStamp = int(time.mktime(timeArray))  # 变成秒，参数必须是元组
    return timeStamp

class samacharjagatSpider(scrapy.Spider):
    name = 'samacharjagat'
    website_id =  1095 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['samacharjagat.com']
    start_urls = ['https://www.samacharjagat.com/',]

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(samacharjagatSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")

        a_list = soup.find("ul", class_="nav navbar-nav").select("li>a")
        for a in a_list[1:]:
            category1_url = a.get("href")
            item['category1'] = a.text
            item['category2'] = None
            yield scrapy.Request(category1_url, callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据
    def get_next_page(self, response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]
            a_list = soup.select("body > div > div > div > div > div > div.col-md-8 > div > div > div.col-md-3 > a")
            for a in a_list:
                yield scrapy.Request(a.get("href"), callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据

            next_url = response.url
            if self.time == None or format_time3(format_time2(soup.select("body > div > div > div > div > div > div.col-md-8 > div > div > div.col-md-9 > div.cat_page > div")[-1].text.strip())) >= int(self.time):
                next_url = next_url.rsplit('/',1)[0]+'/'+soup.find("ul",class_="pager").select("li>a")[-1].get("href") if soup.find("ul",class_="pager")else None
                yield scrapy.Request(next_url, meta=response.meta, callback=self.get_next_page)
            else:
                self.logger.info('时间截止')

    def get_news_detail(self,response):
        '''
        :param response: x新闻正文response
        :return: 新闻页面详情信息
        '''
        item = response.meta["item"]

        soup = bs(response.text, "html.parser")
        temp_time = ''
        pub_time = soup.select_one("body > div.sj_container > div.container-fluid.top_news > div > div.col-md-8.post_heading > div:nth-child(1) > div").text.split("|")[1]  # 文章发布时间   可用Util类中的方法实现。 否则使用"%Y-%m-%d %H:%M:%S"格式保存数据
        for p in pub_time[1:]:
            temp_time += p
        pub_time = format_time2(temp_time)
        images = [img.get("src") for img in soup.find_all("img", hspace="0")]  # body中的图片链接url   要求是字符串的list，如：["url1","url2"...]

        if soup.find("div", class_="col-md-12 feature_image img-responsive"):
            images.append(soup.find("div", class_="col-md-12 feature_image img-responsive").select_one("img").get("src"))

        body = ''  # 文章内容   需要作为一个完整的字符串存入
        for p in soup.select("body > div.sj_container > div.container-fluid.top_news > div > div.col-md-8.post_heading > div:nth-child(4) > div.col-md-12.post_body > p"):
            if p.text != "	":
                body += p.text.strip() + '\n'
        abstract = body.split("।")[0] + body.split("।")[1] if len(body.split("।")) >= 2 else body  # 文章摘要   若没有则默认为文章第一句话

        title = soup.select_one("body > div.sj_container > div.container-fluid.top_news > div > div.col-md-8.post_heading > div > h1").text  # 文章标题
        item['title'] = title
        item['pub_time'] = pub_time
        item['images'] = images
        item['abstract'] = abstract
        item['body'] = body

        yield item
