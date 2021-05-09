
from itemadapter import ItemAdapter
from demo.util import Util
import pymysql
import hashlib
import json

class DemoSqlPipeline:
    keys = ( # sql字段
        'website_id',
        'request_url',
        'response_url',
        'category1',
        'category2',
        'title',
        'abstract',
        'body',
        'pub_time',
        'cole_time',
        'images',
        'language_id',
        'md5'
        )

    def __init__(self):
        self.db = None
        self.cur = None

    def sql_serve(self, item, spider):
        keyString = ''
        valueString = ''
        valuelist = []
        flag = False
        for key in self.keys:
            if(key in item):
                if flag == False:
                    flag = True
                    keyString += str(key)
                    valueString += '%s'
                else:
                    keyString += (','+str(key))
                    valueString += ',%s'
                valuelist.append(item[key])
        sqli = 'insert into news ('+str(keyString)+') values ('+str(valueString)+')'
        # spider.logger.info(sqli)
        self.cur.execute(sqli,valuelist)
        self.db.commit()

    def process_item(self, item, spider):
        m = hashlib.md5() # md5生成
        m.update(item['response_url'].encode(encoding='utf-8'))
        item['md5'] = m.hexdigest()

        item['images'] = json.dumps(item['images'])# images生成

        item['cole_time'] = Util.format_time() # cole_time生成

        self.sql_serve(item,spider) # 数据库insert
        
        return item

    def open_spider(self, spider):
        self.db = pymysql.connect(
            host=spider.sql['host'],
            user=spider.sql['user'],
            password=spider.sql['password'],
            db=spider.sql['db'],
        )
        self.cur = self.db.cursor()

    def close_spider(self, spider):
        self.db.close()

class DemoHtmlPipeline: # 保存网页html到本地
    def process_item(self, item, spider):
        path = '/home/dg/codes/html/' # 本地html仓库地址
        with open(path + item['md5'],'w+',encoding='utf-8') as file:
            file.write(item['html'])
        return item