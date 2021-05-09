# coding=utf-8

import os
import pymysql
import xlwt
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

time_now = time.strftime("%Y-%m-%d",time.localtime(time.time()))
time_yesterday = time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))

sql = { #数据库配置
    'host': "192.168.235.162",
    'user': "dg_admin",
    'password': "dg_admin",
    'db': "dg_crawler"
}
file = '{}.xls'.format(time_yesterday) #文件路径
sender = '2782299413@qq.com' #发送方邮箱
passwd = 'gbslaicivtcvdgab' #授权码
#收件人邮箱
receivers = [
    'gdufs_shuwa@163.com',
    '657742829@qq.com',
    'jiangshengyi@163.com',
    '331423904@qq.com',
    '734200940@qq.com',
    '2397812053@qq.com',
    'chenxuanqi6@163.com',
    '1317787446@qq.com',
    '912100484@qq.com',
    '2656141474@qq.com',
    '1626321547@qq.com',
    '1044880463@qq.com',
    '1024463088@qq.com',
    '2905939881@qq.com',
    '1031482298@qq.com',
    '1197072098@qq.com'
]

def select(execute):
    db = pymysql.connect(sql['host'],sql['user'],sql['password'],sql['db'])
    cursor = db.cursor()
    cursor.execute(execute)
    out = cursor.fetchall()
    db.close()
    return out

def excel(path):
    book = xlwt.Workbook(encoding='utf-8',style_compression=0)

    xlr = book.add_sheet('每日',cell_overwrite_ok=True)
    data = select("select website_id,url,website.c_name,website.e_name,count(news.id),developer,`language`.c_name,country.`name`,website.start_time from ((news left join website on news.website_id = website.id) left join `language` on website.lan_id = `language`.id) left join country on website.country_id = country.id where news.cole_time >= '{}' and news.cole_time < '{}' group by website_id".format(time_yesterday,time_now))
    i = 0
    for x in ['website_id','url','c_name','e_name','num','developer','language','country','start_time']:
        xlr.write(0,i,x)
        i+=1
    i = 1
    for y in data:
        j = 0
        for x in y[:-1]:
            xlr.write(i,j,x)
            j+=1
        xlr.write(i,j,y[-1].strftime('%Y-%m-%d %H:%M:%S')) if y[-1] != None else xlr.write(i,j,'None')
        i+=1
    xlr.write(i+1,0,'总条数')
    xlr.write(i+2,0,select("select count(id) from news where news.cole_time >= '{}' and news.cole_time < '{}'".format(time_yesterday,time_now))[0][0])

    xlr = book.add_sheet('累计',cell_overwrite_ok=True)
    data = select("select website_id,url,website.c_name,website.e_name,count(news.id),developer,`language`.c_name,country.`name`,website.start_time from ((news left join website on news.website_id = website.id) left join `language` on website.lan_id = `language`.id) left join country on website.country_id = country.id group by website_id")
    i = 0
    for x in ['website_id','url','c_name','e_name','num','developer','language','country','start_time']:
        xlr.write(0,i,x)
        i+=1
    i = 1
    for y in data:
        j = 0
        for x in y[:-1]:
            xlr.write(i,j,x)
            j+=1
        xlr.write(i,j,y[-1].strftime('%Y-%m-%d %H:%M:%S')) if y[-1] != None else xlr.write(i,j,'None')
        i+=1
    xlr.write(i+1,0,'总条数')
    xlr.write(i+2,0,select('select count(id) from news')[0][0])

    book.save(path)

def sendmail(pathlist):
    msgRoot = MIMEMultipart()
    msgRoot['Subject'] = '数据部每日报告 '+time_yesterday
    msgRoot['From'] = sender
    msgRoot['To'] = ','.join(receivers)

    part = MIMEText('',_charset="utf-8")
    msgRoot.attach(part)
    for path in pathlist:
        part = MIMEApplication(open(path,'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=path.split('\\')[-1])
        msgRoot.attach(part)

    try:
        s = smtplib.SMTP_SSL('smtp.qq.com',465)
        s.login(sender, passwd)
        s.sendmail(sender, receivers, msgRoot.as_string())
        print ("发送成功")
        s.quit()
    except smtplib.SMTPException:
        print("发送失败")

if __name__ == '__main__':
    excel(file)
    sendmail([file])
    os.remove(file)
