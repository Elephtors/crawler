import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util

class sandhyapravaktaSpider(scrapy.Spider):
    name = 'sandhyapravakta'
    website_id =  1102  # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['sandhyapravakta.com']
    start_urls = ['https://sandhyapravakta.com/',]

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(sandhyapravaktaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()

        soup = bs(response.text, "html.parser")
        for li in soup.select("#menu-td-demo-header-menu-1 > li.menu-item")[1:]:  # 第一个是home不要
            a = li.select_one("a")
            item['category1'] = a.text
            category1_url = a.get("href")

            if li.find("ul", class_="sub-menu"):
                temp_url = []
                # for ul in li.find("ul", class_="sub-menu"):#第一个ul
                item['category2'] = li.find("ul", class_="sub-menu").select_one("a").text
                for ul in li.select("ul>li>ul>li>a"):  # 第2个ul
                    category2_url = ul.get("href")
                    item['category2'] = ul.text
                    if category2_url not in temp_url:
                        temp_url.append(category2_url)
                        # print(category1 + '\t' + category2 + '\t' + category2_url)
                        yield scrapy.Request(category2_url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据
            else:
                if item['category1'] != 'कोरोना अपडेट' and item['category1']!="e-paper":
                    item['category2'] = None
                    yield scrapy.Request(category1_url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据
                    # print(category1 + '\t' + category1_url)

    def get_next_page(self, response):
        soup = bs(response.text, "html.parser")
        content_div = soup.find("div", class_="td-ss-main-content")

        h3_list = content_div.find_all("h3", class_="entry-title td-module-title")
        for h3 in h3_list:
            news_url = h3.select_one("a").get("href")
            yield scrapy.Request(news_url,meta=response.meta,callback=self.get_news_detail)

        if self.time == None or Util.format_time3(Util.format_time2(content_div.find_all("time",class_="entry-date updated td-module-date")[-1].text)) >= int(self.time):
                next_url = soup.find("div",class_="page-nav td-pb-padding-side").select("a")[-1].get("href") if  soup.find("div",class_="page-nav td-pb-padding-side").select("a")[-1].select("i")else None
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
        try:
            title = soup.find("h1", class_="entry-title").text.strip()
            pub_time = soup.select_one("article").find("time", class_="entry-date updated td-module-date").text
            body = ''
            for p in soup.select_one("article").select("p"):
                body += p.text
            abstract = body.split("।", 1)[0]
            item["title"] = title
            item["pub_time"] = Util.format_time2(pub_time)
            item["abstract"] = abstract
            item["body"] = body
            image_list = [img.get("src") for img in soup.find("div", class_="td-post-featured-image").select("img")]
            item["images"] = image_list
        except Exception:
            pass
        yield item