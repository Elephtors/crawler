import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util
import time
from datetime import datetime
import re
def format_time2(s):
    '''

    :param s:原时间格式为19 March 2021 9:52 AM
    :return: 返回2021-03-19 09:52:00
    '''
    pub_time = re.split(" |,|:|-|th|st|nd|rd", s)

    #文章里的时间切割完之后变这样['Aug', '19', '', '', '2010', '10', '33', 'am']
    # 翻页那里的时间切割王之后变成这样['October', '12', '', '2020']
    month = pub_time[1]
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
    year = pub_time[2]
    day = pub_time[0]
    hour = pub_time[-3] if pub_time[-1] == 'AM' else int(pub_time[-3]) + 12
    if hour == 24:
            hour = 12
    minute = pub_time[-2]

    return time.strftime("%Y-%m-%d %H:%M:%S",datetime(int(year), month, int(day), int(hour), int(minute)).timetuple())

class haribhoomiSpider(scrapy.Spider):
    name = 'haribhoomi'
    website_id =  984 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['haribhoomi.com']
    start_urls = ['https://www.haribhoomi.com/',]

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(haribhoomiSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''

        soup = bs(response.text, 'html.parser')
        url_list = []
        all_ul = soup.select_one("#sticky > div > div > div > div.main-menu.navbar-collapse.collapse > nav > ul")
        for li in all_ul.select("li"):
            if li.select_one("a").get("href") == "/live-tv":
                break
            a_list = li.select("a")
            for a in a_list:
                url = self.start_urls[0] + a.get("href").split('/', 1)[1]
                if url not in url_list:
                    url_list.append(url)
        for this_url in url_list:

            yield scrapy.Request(this_url, callback=self.get_next_page)

    def get_next_page(self, response):

            soup = bs(response.text, "html.parser")
            if soup.find(text="View All"):
                body_div = soup.find("div", class_="news_listing_main_v2")

                div_list = body_div.find_all("div", class_="list_content")

                for div in div_list:
                    article_url = self.start_urls[0].rsplit('/', 1)[0] + div.select_one("a").get("href")
                    yield scrapy.Request(article_url, callback=self.get_news_detail)

                temp_time = div_list[-1].find("span", class_="convert-to-localtime").text.split(" GMT")[0]

                if self.time == None or Util.format_time3(format_time2(temp_time)) >= int(self.time):

                        next_url = soup.find("a",class_="page-numbers next last page-numbers").get("href") if soup.find("a",class_="page-numbers next last page-numbers") else None

                        if next_url:
                                yield scrapy.Request(next_url, callback=self.get_next_page)
                else:
                    self.logger.info('时间截止')
            else:
                self.logger.info("这还有二级目录！！！！！！")

    def get_news_detail(self,response):
        '''
        :param response: x新闻正文response
        :return: 新闻页面详情信息
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")
        main_html = soup.select_one("#details-page-infinite-scrolling-data")
        image_list = []
        content_html = main_html.find("div", class_="story_content")

        title = soup.find("h1").text.strip()
        pub_time = soup.find_all("span", class_="convert-to-localtime")[0].text.split(" GMT")[0]
        image_list.append(main_html.find("div", class_="image-wrap-article").select_one("img").get("src"))
        for img in content_html.find_all("h-img", class_="hocalwire-draggable"):
            image_list.append(img.get("src"))
        body = ''
        for p in content_html.find_all("p"):
            body += (p.text.strip() + '\n')

        abstract = soup.find("h2", class_="desc_data").text.strip() if soup.find("h2", class_="desc_data") else body.split("।", 1)[0]

        item['category1'] = soup.find("div", class_="tag-block").select("a")[1].text.split('>')[0].strip() if soup.find("div", class_="tag-block").select("a") else ''
        item['category2'] = soup.find("div", class_="tag-block").select("a")[2].text.split('>')[0].strip() if len(soup.find("div", class_="tag-block").select("a")) == 3 else ''
        item["title"] = title
        item["pub_time"] = format_time2(pub_time.strip())
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item