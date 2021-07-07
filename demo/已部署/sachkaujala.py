import scrapy
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from demo.util import Util

class sachkaujalaSpider(scrapy.Spider):
    name = 'sachkaujala'
    website_id =  1124 # 网站的id(必填)
    language_id = 1930  # 所用语言的id

    allowed_domains = ['sachkaujala.com']
    start_urls = ['https://sachkaujala.com/',]
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(sachkaujalaSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        '''
        :param response:
        :return:一级目录链接
        '''
        item = DemoItem()
        soup = bs(response.text, "html.parser")

        a_list = soup.find("ul", class_="menu").select("a")
        for a in a_list[1:-1]:
            url = a.get("href")
            item['category1'] = a.text.strip()
            item['category2'] = ''
            yield scrapy.Request(url, callback=self.get_next_page,meta={"item": item})  # 层与层之间通过meta参数传递数据

    def get_next_page(self, response):

            item = response.meta["item"]
            soup = bs(response.text, "html.parser")
            top_article = soup.find("div", class_="herald-section container herald-no-sid").find_all("a",
                                                                                                     class_="fa-post-thumbnail")
            for a in top_article:
                article_url = a.get("href")
                # print(article_url)
                yield scrapy.Request(article_url, meta=response.meta, callback=self.get_news_detail)

            for a in soup.find("div", class_="row row-eq-height herald-posts").find_all("h2"):
                article_url = a.select_one("a").get("href")
                # print(article_url)
                yield scrapy.Request(article_url,meta=response.meta,callback=self.get_news_detail)

            temp_time = soup.find("div",class_="row row-eq-height herald-posts").find_all("span",class_="updated")[-1].text if soup.find("div",class_="row row-eq-height herald-posts") else "January 1, 1970"

            if self.time == None or Util.format_time3(Util.format_time2(temp_time)) >= int(self.time):

                        #排除到最后一页的情况
                    next_url = soup.find("a",text='Older Entries').get("href") if soup.find("a",text='Older Entries') else None
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
        title = soup.find("h1", class_="entry-title h1").text
        pub_time = soup.find("header", class_="entry-header").find("span", class_="updated").text
        images = []
        if soup.find("div", class_="herald-post-thumbnail herald-post-thumbnail-single"):
            for img in soup.find("div", class_="herald-post-thumbnail herald-post-thumbnail-single").select("img"):
                if img.get("src").split(":")[0] != 'data':
                    images.append(img.get("src"))
        body = ''
        if soup.find("div", class_="entry-content herald-entry-content").find("p"):
            for p in soup.find("div", class_="entry-content herald-entry-content").find_all({"p", "h3"}):
                body += (p.text.strip() + '\n')
        else:
            for p in soup.find("div", class_="entry-content herald-entry-content").select("div")[1:-1]:  # 最后一个是空白
                body += (p.text.strip() + '\n')
        abstract = body.split("।", 1)[0]
        item["title"] = title
        item["pub_time"] = Util.format_time2(pub_time)
        item["images"] = images
        item["abstract"] = abstract
        item["body"] = body
        yield item