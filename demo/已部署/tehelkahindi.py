import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util

class tehelkahindiSpider(scrapy.Spider):
    name = 'tehelkahindi'
    website_id =  1099 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['tehelkahindi.com']
    start_urls = ['http://tehelkahindi.com/',]

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(tehelkahindiSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")
        for li in soup.select("#menu-main-menu-1 > li.menu-item")[1:-2]:
            a = li.select_one("a")
            item['category1'] = a.text
            category1_url = a.get("href")

            if li.find("ul", class_="sub-menu"):
                for sub_a in li.find("ul", class_="sub-menu").select("a"):
                    item['category2'] = sub_a.text
                    category2_url = sub_a.get("href")

                    yield scrapy.Request(category2_url,callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据
            else:
                item['category2'] = None
                yield scrapy.Request(category1_url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据


    def get_next_page(self, response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]
            a_list = soup.find_all("a", class_="td-image-wrap")
            for a in a_list:
                yield scrapy.Request(a.get("href"), callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据

                if self.time == None or Util.format_time3(Util.format_time2(soup.find_all("time",class_="entry-date updated td-module-date")[-1].text)) >= int(self.time):
                    next_url = soup.find("div", class_="page-nav td-pb-padding-side").select("a")[-1].get("href") if soup.find("div", class_="page-nav td-pb-padding-side") else None
                    if next_url:
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

        title = soup.find("h1", class_="entry-title").text
        pub_time = Util.format_time2(soup.find("time", class_="entry-date updated td-module-date").text)
        image_list = [img.get("src") for img in soup.find_all("img", class_="entry-thumb td-modal-image")] if soup.find("img", class_="entry-thumb td-modal-image") else None
        body = ''
        for p in soup.find("div", class_="td-post-content").select("p"):
            body += (p.text + '\n')

        abstract = body.split("।")[0]

        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body

        yield item