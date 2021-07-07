import time
from datetime import datetime
import re

class Util(object):

    month = {
        'January': 1,
        'February': 2,
        'March': 3,
        'April': 4,
        'May': 5,
        'June': 6,
        'July': 7,
        'August': 8,
        'September': 9,
        'October': 10,
        'November': 11,
        'December': 12,
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sept': 9,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }

    @staticmethod
    def format_time(t=0):
        if t == 0:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        else:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

    @staticmethod
    def format_time2(data1):
        data = ''
        list = [i for i in re.split('/| |,|:|\n|\r|\f|\t|\v',data1) if i!='']
        for i in list:
            data += (i+' ')
        data = data.strip()
        if re.findall(r'\S+ \d+ \d+ \d+ \d+',data) != []:
            num = 0
            while list[num] not in Util.month.keys():
                num += 1
            return time.strftime("%Y-%m-%d %H:%M:%S", datetime(int(list[num+2]),Util.month[list[num]],int(list[num+1]),int(list[num+3]),int(list[num+4])).timetuple())
        elif re.findall(r'\S+ \d+ \d+',data) != []:
            num = 0
            while list[num] not in Util.month.keys():
                num += 1
            return time.strftime("%Y-%m-%d %H:%M:%S", datetime(int(list[num+2]),Util.month[list[num]],int(list[num+1])).timetuple())
        elif re.findall(r'\d+ hours ago',data) != [] or re.findall(r'\d+ hour ago',data) != []:
            num = 0
            while re.findall(r'\d+',list[num])==[]:
                num += 1
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()-int(list[num])*3600))
        elif re.findall(r'\d+ days ago',data) != [] or re.findall(r'\d+ day ago',data) != []:
            num = 0
            while re.findall(r'\d+',list[num])==[]:
                num += 1
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()-int(list[num])*86400))
        elif re.findall(r'\d+ weeks ago',data) != [] or re.findall(r'\d+ week ago',data) != []:
            num = 0
            while re.findall(r'\d+',list[num])==[]:
                num += 1
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()-int(list[num])*604800))
        elif re.findall(r'\d+ months ago',data) != [] or re.findall(r'\d+ month ago',data) != []:
            num = 0
            while re.findall(r'\d+',list[num])==[]:
                num += 1
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()-int(list[num])*2592000))
        elif re.findall(r'\d+ years ago',data) != [] or re.findall(r'\d+ year ago',data) != []:
            num = 0
            while re.findall(r'\d+',list[num])==[]:
                num += 1
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()-int(list[num])*31536000))
        else:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    @staticmethod
    def format_time3(data):
        timeArray = time.strptime(data, "%Y-%m-%d %H:%M:%S") 
        timeStamp = int(time.mktime(timeArray))
        return timeStamp