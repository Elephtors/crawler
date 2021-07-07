import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup
from scrapy.http import Request, FormRequest
import re
import json

class bworldonlineSpider(scrapy.Spider):
    name = 'bworldonline'
    website_id = 191 # 网站的id(必填)
    language_id = 1866 # 所用语言的id
    start_urls = ['https://www.bworldonline.com/']
    sql = {  # sql配置
        'host': '192.168.235.162',
        'user': 'dg_admin',
        'password': 'dg_admin',
        'db': 'dg_crawler'
    }

    data = {
    'action': 'td_ajax_loop',
    'loopState[sidebarPosition]': '',
    'loopState[moduleId]': 'td_module_category_list',
    'loopState[currentPage]': '1',
    'loopState[max_num_pages]': '0',
    'loopState[atts][category_id]': '0',
    'loopState[atts][offset]': '3',
    'loopState[ajax_pagination_infinite_stop]': '0',
    'loopState[server_reply_html_data]': ''
    }
    url = 'https://www.bworldonline.com/wp-admin/admin-ajax.php?td_theme_name=Newsmag&v=3.3.1'

    def __init__(self, time=None, *args, **kwargs):
        super(bworldonlineSpider, self).__init__(*args, **kwargs) # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        html = BeautifulSoup(response.text)
        for i in html.select('#menu-main-menu > li > a[href^="https://www.bworldonline.com/category/"]'):
            yield Request(i.attrs['href'], callback=self.parse1)

    def parse1(self, response):
        html = BeautifulSoup(response.text)
        list = response.url.split('/')
        meta = {
            'category1' : list[4],
            'category2' : list[5],
        }
        for i in html.select('.td-pb-span12 .td-big-grid-wrapper .td-module-thumb > a'):
            yield Request(i.attrs['href'],meta=meta, callback=self.parse_item)

        meta['data'] = self.data
        meta['data']['loopState[atts][category_id]'] = re.findall(r'\'category_id\':(\d+)',response.text)[0]
        meta['page'] = 1
        yield FormRequest(self.url,formdata=meta['data'],meta=meta,callback=self.parse2)
        

    def parse2(self, response):
        text = json.loads(response.text)['server_reply_html_data']
        html = BeautifulSoup(text)
        for i in html.select('.td_module_category_list.td_module_wrap.td-meta-info-hide .td-module-thumb > a')[:-1]:
            yield Request(i.attrs['href'],meta=response.meta, callback=self.parse_item)
        response.meta['dont_filter'] = True
        yield Request(html.select('.td_module_category_list.td_module_wrap.td-meta-info-hide .td-module-thumb > a')[-1].attrs['href'], meta=response.meta, callback=self.parse_time, dont_filter=True)

    def parse_time(self, response):
        html = BeautifulSoup(response.text)
        response.meta['dont_filter'] = False
        if self.time == None or Util.format_time3(Util.format_time2(html.select('.td-post-date > time')[0].text)) >= int(self.time):
            response.meta['page'] += 1
            response.meta['data']['loopState[currentPage]'] = str(response.meta['page'])
            yield FormRequest(self.url,formdata=response.meta['data'],meta=response.meta,callback=self.parse2)
        else:
            self.logger.info('截止')
        yield Request(response.url,meta=response.meta, callback=self.parse_item)

    def parse_item(self, response):
        html = BeautifulSoup(response.text)
        item = DemoItem()
        item['title'] = html.select('.entry-title')[0].text
        item['category1'] = response.meta['category1']
        item['category2'] = response.meta['category2']
        item['body'] = ''
        flag = False
        for i in html.select('.td-post-content-area .column-meta ~ p'):
            item['body'] += (i.text+'\n')
            if i.text != '' and flag == False:
                flag = True
                item['abstract'] = i.text
        item['pub_time'] = Util.format_time2(html.select('.td-post-date > time')[0].text)
        if html.select('.td-post-content-area .td-post-featured-image img') != []:
            item['images'] = [html.select('.td-post-content-area .td-post-featured-image img')[0].attrs['src'],]
        yield item
