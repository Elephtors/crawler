
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import json

# 将爬虫类名和name字段改成对应的网站名
class spin_Spider(scrapy.Spider):
    name = 'spin'
    website_id = 1192 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.spin.ph/?ref=nav', 'https://www.spin.ph/life?ref=nav']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(spin_Spider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        meta = {}
        meta["category1"] = ''
        meta["category2"] = ''
        meta["page"] = 1
        soup = BeautifulSoup(response.text, "html.parser")
        if response.url == 'https://www.spin.ph/?ref=nav':  # 判断是sport还是life网页
            meta['category1'] = 'sport'
        else:
            meta['category1'] = 'life'
        judge_url = soup.select("#menu-guide-subchs > li")
        finall_all_url = []
        all_modle = []
        if judge_url != []:  # 将life里的包弄出来
            for li in soup.select("#menu-guide-subchs > li"):
                u = li.find("a").get("href").split("?")[0].split("/")[-1]
                all_modle.append(u)
            for li in soup.select("#menu-active-lifestyle-subchs > li"):
                u = li.find("a").get("href").split("?")[0].split("/")[-1]
                all_modle.append(u)
            for li in soup.select("#menu-people-subchs > li"):
                u = li.find("a").get("href").split("?")[0].split("/")[-1]
                all_modle.append(u)
            for li in soup.select("#menu-cars-and-tech-subchs > li"):
                u = li.find("a").get("href").split("?")[0].split("/")[-1]
                all_modle.append(u)
            for i in range(len(all_modle)):
                life_modle = 'https://api.summitmedia-digital.com/spin/v1/channel/get/{}/1/6'
                finall_url_sport = life_modle.format(all_modle[i])
                finall_all_url.append(finall_url_sport)
        else:  # 计划是将sport里面的包弄出来
            modle_sport = ["american-football", "athletics", "badminton", "baseball", "basketball", "billiards", "bowling",
                           "boxing", "cheerdance", "chess", "cycling", "dragon-boat", "extreme-sports", "football", "golf",
                           "gymnastics", "horse-racing", "karatedo", "lifestyle", "mma", "moto-racing", "multisport", "polo",
                           "rugby", "running", "sailing", "softball", "swimming", "taekwondo", "volleyball", "wrestling",
                           "tennis", "triathlon", "weightlifting", "winter-sports"]
            for i in range(len(modle_sport)):
                zhuabao_url = 'https://api.summitmedia-digital.com/spin/v1/channel/get/{}/1/6'
                finall_url_sport = zhuabao_url.format(modle_sport[i])
                finall_all_url.append(finall_url_sport)
        for url_one in finall_all_url:
            yield scrapy.Request(url_one, meta=meta, callback=self.pares_category2)

    def pares_category2(self, response):  # 对数据包的处理和分析
        result = json.loads(response.text)
        modle_url = 'https://www.spin.ph'
        all_url = []
        all_time = []
        for i in result:
            url = i["url"]  # 获取文章中的url
            if i["channel"]["parent"]:
                name = i["channel"]["parent"]["name"]  # 获取二级目录
            else:
                name = i["channel"]["name"]  # 获取二级目录
            response.meta['category2'] = name
            datetime = i['date_published']
            need_url = modle_url + url
            all_url.append(need_url)
            all_time.append(datetime)
        for url1 in all_url:
            yield scrapy.Request(url1, meta=response.meta, callback=self.pares_article)
        if all_time != []:
            need_time = int(all_time[-1])
            if self.time == None or need_time >= int(self.time):
                next_url = str(response.url).split("/")[0:-2]
                need_url2 = '/'.join(next_url)
                response.meta['page'] += 1
                yield scrapy.Request(need_url2 + '/' + str(response.meta['page']) + '/6', meta=response.meta, callback=self.pares_category2)
            else:
                self.logger.info('时间截止')

    def pares_article(self, response):
        item = DemoItem()
        soup = BeautifulSoup(response.text, "html.parser")
        images = []
        picture = soup.find("div", {"class": "artl__head"})
        pic = picture.find("img").get("src") if picture and picture.find("img") else None
        if pic:
            images.append(pic)

        datetime = soup.find("meta", {"property": "published_time"})
        if datetime:  # 具体到每个文章中可能没有时间，所有拿到的发布时时间精确到分
            datetime = datetime.get("content")
            time = datetime.replace(":", ".").replace(",", ".").replace(" ", "")
            time = time.split(".")
            pub_time = ("20{}-{}-{} {}:{}:00".format(time[4], time[3], time[2], time[0], time[1]))  # 已经添加秒
        else:
            pub_time = Util.format_time()

        title = soup.find("h1").text.strip() if soup.find("h1") else None
        body_list = []
        temp_list = soup.select('.wrap__ctnt p')
        for temp in temp_list:
            [s.extract() for s in temp('div')]
            [s.extract() for s in temp('label')]
            if temp.text and temp.text != '\n':
                body_list.append(temp.text.strip())
        item['body'] = '\n'.join(body_list)
        abstract = body_list[0] if body_list else None

        item["images"] = images
        item["category1"] = response.meta["category1"]
        item["category2"] = response.meta["category2"]
        item['title'] = title
        item['pub_time'] = pub_time
        item['abstract'] = abstract
        yield item
