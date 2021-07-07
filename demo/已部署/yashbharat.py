import scrapy
from demo.items import DemoItem
from demo.util import Util
from bs4 import BeautifulSoup as bs

class yashbharat(scrapy.Spider):
    name = 'yashbharat'
    website_id =  1073 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['yashbharat.com']
    start_urls = ['http://www.yashbharat.com/']

    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }
    def __init__(self, time=None, *args, **kwargs):
        super(yashbharat, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()
        soup = bs(response.text, "html.parser")

        div = soup.find("div", class_="menu-primary-container")
        li_list = div.select("ul>li")
        category2_list = []
        for li in li_list[1:-1]:  # home_url和“关于我们”不要
            category1 = li.select_one("a").text
            if li.select_one("a").text == "ई-पेपर" or li.select_one("a").text in category2_list:
                pass
            else:
                item['category1'] = category1
                if li.select_one("ul") != None:
                    # print(li.select_one("ul"))

                    a_list = li.select("ul>li>a")
                    for a in a_list:
                        if a.text == category1:
                            pass
                        else:
                            category2 = a.text
                            item['category2'] = category2
                            category2_list.append(category2)
                            category_url = a.get("href")
                            yield scrapy.Request(category_url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据
                else:
                    item['category2'] = ''
                    url = li.select_one("a").get("href")
                    yield scrapy.Request(url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据
    
    def get_next_page(self, response):
            soup = bs(response.text, "html.parser")
            item = response.meta["item"]
            div = soup.find("div", class_="article-container")
            article_list = div.select("article")
            for article in article_list:
                    article_url = article.select_one("a").get("href")
                    yield scrapy.Request(article_url, callback=self.get_news_detail, meta={"item": item})  # 层与层之间通过meta参数传递数据

            if self.time == None or Util.format_time3(Util.format_time2(soup.select('.article-container > article time')[-1].text)) >= int(self.time):
                url = soup.find("li",class_="previous").select_one("a").get("href") if soup.find("li",class_="previous").select_one("a").get("href") else None
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
        title = soup.find("h1", class_="entry-title").text.strip() if soup.find("h1", class_="entry-title") else None
        pub_time = Util.format_time2(soup.find("time", class_="entry-date published updated").text) if soup.find("time",class_="entry-date published updated") else None
        image_list = [img.get("src") for img in soup.find_all("img",class_="attachment-colormag-featured-image size-colormag-featured-image wp-post-image")] if soup.find_all("img", class_="attachment-colormag-featured-image size-colormag-featured-image wp-post-image") else None
        abstract = soup.find("div", class_="entry-content clearfix").select_one("p").text.split("।")[0]  # 正文第一句话为摘要
        body = ''
        for p in soup.find("div", class_="entry-content clearfix").select("p"):
            body += (p.text + '\n')
        item["title"] = title
        item["pub_time"] = pub_time
        item["images"] = image_list
        item["abstract"] = abstract
        item["body"] = body
        yield item
