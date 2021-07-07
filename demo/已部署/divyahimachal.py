import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
import re
from datetime import datetime
import time

def format_time3(data):
    timeArray = time.strptime(data, "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp
def format_time2(s):
    '''

    :param s:原时间格式为Aug 19th, 2010 10:33 am
    :return: 返回2020-11-24 9:42:00
    '''
    pub_time = re.split(" |,|:|-|th|st|nd|rd", s)
    #文章里的时间切割完之后变这样['Aug', '19', '', '', '2010', '10', '33', 'am']
    # 翻页那里的时间切割王之后变成这样['October', '12', '', '2020']
    month = pub_time[0]
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
    elif month == "January":
        month = 1
    elif month == "Febuary":
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
    if len(pub_time)>4:
        year = pub_time[4]
        day = pub_time[1]
        hour = pub_time[-3] if pub_time[-1] == 'am' else int(pub_time[-3]) + 12
        if hour == 24:
            hour = 12
        minute = pub_time[-2]
        return time.strftime("%Y-%m-%d %H:%M:%S",datetime(int(year), month, int(day), int(hour), int(minute)).timetuple())
    else:
        year = pub_time[3]
        day = pub_time[1]
        return time.strftime("%Y-%m-%d %H:%M:%S",datetime(int(year), month, int(day)).timetuple())

class divyahimachalSpider(scrapy.Spider):
    name = 'divyahimachal'
    website_id =  1091 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['divyahimachal.com']
    start_urls = ['https://www.divyahimachal.com/',]

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(divyahimachalSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")
        url_list = []
        for li in soup.find("ul", class_="navbar left").select("li")[1:-1]:  # home，DH电视不要，电子纸不要
            category1_url = li.select_one("a").get("href")
            category1 = li.select_one("a").text
            if category1 == 'Epaper':  # 去掉电子报
                pass
            else:
                if li.select_one("ul"):
                    category2_list = li.select("ul>li>a")
                    for a in category2_list[1:]:
                        category2_url = 'https://www.divyahimachal.com'+a.get("href")
                        item['category2'] = a.text
                        item['category1'] = category1
                        if category2_url not in url_list:
                            url_list.append(category2_url)
                            # print(category1 + '\t' + category2 + '\t' + url + category2_url)
                            yield scrapy.Request(category2_url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据
                else:
                    if category1_url not in url_list:
                        item['category2'] = None
                        yield scrapy.Request('https://www.divyahimachal.com'+category1_url, callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据
    def get_next_page(self, response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]
            first_url = soup.find("div", class_="o-topnewsnew").select_one("a").get("href")
            yield scrapy.Request(first_url, callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据

            div_list = soup.find_all("div", class_="frame left")
            for div in div_list:
                news_url = div.select_one("a").get("href")
                yield scrapy.Request(news_url, callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据
            if self.time == None or format_time3(format_time2(soup.find_all("span", class_="byline")[-1].text.split(" ", 1)[1])) >= int(self.time):
                url = soup.find("a",class_="next page-numbers").get("href") if soup.find("a",class_="next page-numbers").get("href")else None
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
        # item={}
        body_div = soup.find("div", class_="content-body")
        title = soup.find("article", class_="storybox").select_one("h1").text
        pub_time = format_time2(soup.find_all("span")[7].text.strip())
        image_list = [img.get("src") for img in soup.find_all("img",class_="attachment-post-thumbnail size-post-thumbnail wp-post-image")] if soup.find("img", class_="attachment-post-thumbnail size-post-thumbnail wp-post-image") else None
        body = ''
        for p in body_div.select("p"):
            body += (p.text + '\n')
        abstract = body_div.select_one("p>strong").text.strip() if body_div.select_one("p>strong") else body.split("।")[0]
        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item
