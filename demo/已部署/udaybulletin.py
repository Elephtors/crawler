
# 此文件包含的头文件不要修改
import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, Response
import json
import time

#将爬虫类名和name字段改成对应的网站名
class liveakhbar(scrapy.Spider):
    name = 'udaybulletin'
    website_id = 941 # 网站的id(必填)
    language_id = 1930 # 所用语言的id
    start_urls = ['https://www.udaybulletin.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    # 这是类初始化函数，用来传时间戳参数
    def __init__(self, time=None, *args, **kwargs):
        super(liveakhbar, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    ##需补充爬取时间代码
    def judge_time(self,time_pub):
        if self.time == None or int(self.time) <= time_pub:
            return True
        else:
            return False

    url_move = 'https://www.udaybulletin.com/api/v1/collections/{}?item-type=story&offset={}&limit=10'

    #修改后的函数
    def parse(self,response):
        meta = {}
        html = BeautifulSoup(response.text)
        for category1 in html.select('div.header-three-m__default-menu__24xMV>ul>li'):
            meta['category1'] = category1.select_one('a').text
            categories_2 = category1.select('ul>li>a')
            if categories_2:
                for category2 in categories_2:
                    meta['offset_num'] = 10
                    meta['category2'] = category2.text
                    if meta['category2'] == 'ऑटोमोबाइल' or meta['category2'] == 'अन्य खबर' or meta['category2'] == 'अन्य खेल':
                        continue
                    if meta['category1'] == 'खेल':
                        meta['url_format_content'] = category2.attrs['href'].split('/')[-1] + '-' + category1.select_one('a').attrs['href'].split('/')[-1]
                        yield Request(url=self.url_move.format(meta['url_format_content'],str(meta['offset_num'])),meta=meta,callback=self.parse_passage)
                    else:
                        meta['url_format_content'] = category2.attrs['href'].split('/')[-1]
                        yield Request(url=self.url_move.format(meta['url_format_content'],str(meta['offset_num'])),meta=meta,callback=self.parse_passage)
            else:
                meta['category2'] = None
                meta['offset_num'] = 10
                meta['url_format_content'] = category1.select_one('a').attrs['href'].split('/')[-1]
                yield Request(url=self.url_move.format(meta['url_format_content'],str(meta['offset_num'])),meta=meta,callback=self.parse_passage)

    def parse_passage(self,response):
        all_response = json.loads(response.text)
        flag = True
        ##需要测试一下
        for number in all_response['items']:
            url = number['story']['url']
            response.meta['title'] = number['story']['headline']
            if self.judge_time(int(int(number['story']['content-updated-at']) / 1000)):
                #爬取网页信息
                response.meta['pub_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(number['story']['content-created-at'] / 1000))
                yield Request(url=url,meta=response.meta,callback=self.parse_item)
            else:
                self.logger.info("时间截止！！！！！！！！！！！！")
                flag = False
                break
        if flag:
            response.meta['offset_num'] += 10
            yield Request(url=self.url_move.format(response.meta['url_format_content'],str(response.meta['offset_num'])),meta=response.meta,callback=self.parse_passage)
            ##翻页

    def parse_item(self,response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['title'] = response.meta['title']
        try:
            item['abstract'] = html.find('div',attrs={'class':'p-alt arr--sub-headline arrow-component subheadline-m__subheadline__3H1ig subheadline-m__dark__31XBm'}).text
        except:
            item['abstract'] = None
        item['pub_time'] = response.meta['pub_time']
        body = ''
        for i in html.select('.arr--story-page-card-wrapper p'):
            body = body + i.text + '\n'
        item['body'] = body
        try:
            item['images'] = [html.select_one('figure img').attrs['data-src']]
        except:
            item['images'] = None
            self.logger.info('该文章没有图片！！！！')
        return item



    #def parse(self, response):
    #    meta = {}
    #    html = BeautifulSoup(response.text)
    #    all_ = html.select_one('div.header-three-m__default-menu__24xMV')
    #    all_category1_no_category2 = all_.select('li.menu-m__menu-item__2noyy')
    #    all_category1_have_category2 = all_.find_all('li',attrs={'class':'menu-m__menu-item__2noyy menu-m__has-child__5v4PA'})
    #    for category_1 in all_category1_no_category2:
    #        meta['category1'] = category_1.select_one('a').text
    #        meta['category2'] = None
    #        meta['offset_num'] = 10
    #        url_format_content = category_1.select_one('a').attrs['href'].split('/')[-1]
    #        yield Request(url=self.url_move.format(url_format_content,'10'),meta=meta,callback=self.parse_passage)

        ##想一下怎么处理一些没有内容的网页
    #    for category__1 in all_category1_have_category2:
    #        meta['category1'] = category__1.select_one('a').text
    #        meta['offset_num'] = 10
    #        categories_2 = category__1.select('li.menu-m__sub-menu-item__3HiBx a')
    #        for category_2 in categories_2:
    #             meta['category2'] = category_2.text
    #            if meta['category2'] == 'ऑटोमोबाइल' or meta['category2'] == 'अन्य खबर' or meta['category2'] == 'अन्य खेल':
    #                continue
    #            if meta['category1'] == 'खेल':
    #                meta['url_format_content'] = category_2.attrs['href'].split('/')[-1] + '-' + category__1.select_one('a').attrs['href'].split('/')[-1]
    #                yield Request(url=self.url_move.format(meta['url_format_content'],str(meta['offset_num'])),meta=meta,callback=self.parse_passage)
    #            else:
    #                meta['url_format_content'] = category_2.attrs['href'].split('/')[-1]
    #                yield Request(url=self.url_move.format(meta['url_format_content'],str(meta['offset_num'])),meta=meta,callback=self.parse_passage)
