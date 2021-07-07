import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util

class dunvalleymailSpider(scrapy.Spider):
    name = 'dunvalleymail'
    website_id =  1126 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['dunvalleymail.com']
    start_urls = ['http://dunvalleymail.com/',]
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(dunvalleymailSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")

        world_url = soup.select_one("#menu-td-demo-header-menu-1 > li.menu-item.menu-item-type-taxonomy.menu-item-object-category.td-menu-item.td-normal-menu.menu-item-1078 > a").get("href")
        yield scrapy.Request(world_url, callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据

        for div in soup.find_all("div", class_="block-mega-child-cats"):
            for a in div.select("a"):
                url = a.get("href")

                yield scrapy.Request(url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据

        gadgets_url = soup.select_one("#menu-td-demo-header-menu-1 > li.menu-item.menu-item-type-taxonomy.menu-item-object-category.td-menu-item.td-mega-menu.menu-item-1619 > a").get("href")
        yield scrapy.Request(gadgets_url, callback=self.get_next_page, meta={"item": item})  # 层与层之间通过meta参数传递数据

    def get_next_page(self, response):

            item = response.meta["item"]
            soup = bs(response.text, "html.parser")
            #len(soup.find("div", class_="entry-crumbs").select("i"))代表有几级目录
            item['category1'] = soup.find("div", class_="entry-crumbs").find("span",class_="td-bred-no-url-last").text if len(soup.find("div", class_="entry-crumbs").select("i")) == 1 else soup.find("div", class_="entry-crumbs").select("span")[-2].text
            item['category2'] = soup.find("div", class_="entry-crumbs").find("span",class_="td-bred-no-url-last").text if len(soup.find("div", class_="entry-crumbs").select("i")) != 1 else " "
            for h3 in soup.find("div", class_="td-big-grid-wrapper").select("h3"):
                article_url = h3.select_one("a").get("href")

                yield scrapy.Request(article_url,meta=response.meta,callback=self.get_news_detail)

            for h3 in soup.select_one("#td-outer-wrap > div.td-main-content-wrap > div > div > div.td-pb-span8.td-main-content > div").find_all("h3", class_="entry-title td-module-title"):
                article_url = h3.select_one("a").get("href")

                yield scrapy.Request(article_url,meta=response.meta,callback=self.get_news_detail)

            temp_time = soup.find_all("div",class_="td-block-span6")[-1].select("time")[-1].text if soup.find_all("div",class_="td-block-span6") else "January 1, 1970"

            if self.time == None or Util.format_time3(Util.format_time2(temp_time)) >= int(self.time):
                    next_url = None
                    if soup.find("div", class_="page-nav td-pb-padding-side"):#排除没有页面条的情况
                        #排除到最后一页的情况
                        next_url = soup.find("div",class_="page-nav td-pb-padding-side").select("a")[-1].get("href") if soup.find("div",class_="page-nav td-pb-padding-side").select("a")[-1].select("i") else None
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

        title = soup.find("header", class_="td-post-title").select_one("h1").text
        pub_time = soup.find("header", class_="td-post-title").select_one("time").text

        image_list = []
        if soup.find("div", class_="td-post-featured-image"):
            image_list = [a.select_one("img").get("src") for a in soup.find("div", class_="td-post-featured-image").select("a")]
        body = ''
        part = soup.find("div", class_="td-post-content").select("p") if soup.find("div",class_="td-post-content").select("p") else soup.find("div", class_="td-post-content").select("div")
        for p in part:
            body += (p.text + '\n')
        abstract = body.split("।", 1)[0]
        item["title"] = title
        item["pub_time"] = Util.format_time2(pub_time)
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item