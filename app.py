# coding: utf-8

import datetime

from flask import Flask
from flask import render_template
from flask_sockets import Sockets
# add request 
from flask import request

from views.todos import todos_view

import os
import sys
import urllib2
import requests
import re
import random
from lxml import etree

from Bmob import *
# add for qiniu storage 
from qiniu import Auth, put_file, etag, put_stream, put_data
from qiniu import BucketManager
import qiniu.config
import json
#add for silver price monitoring
import leancloud 


# define a Model ,之前用于today新闻推送，现在已废弃
'''
class New(BmobModel):
    title = '' # title 
'''

# global 
# baseTime_borrow = datetime(2019,datetime.datetime.now().month,datetime.datetime.now().day+1,16,0,0)    # 用于borrow日期校准

# end of Bmob thing 

app = Flask(__name__)

# 动态路由
app.register_blueprint(todos_view, url_prefix='/todos')


def str2int(s):
    def fn(x,y):
        return x*10+y
    def char2num(s):
        return {'0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9}[s]
    return reduce(fn,map(char2num,s))

def parseint(string):
    return int(''.join([x for x in string if x.isdigit()]))

def formpayload(content):
    payloadData = {"text":content}
    return payloadData

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/time')
def time():
    return str(datetime.datetime.now())

## 之前用于todaypro的新闻推送服务,已废弃
'''
@app.route('/news')
def news():
    url = "http://news.163.com/rank/"
    myPage = requests.get(url).content.decode("gbk")
    myPageResults =  re.findall(r'<div class="titleBar" id=".*?"><h2>(.*?)</h2><div class="more"><a href="(.*?)">.*?</a></div></div>', myPage, re.S)
    news = []
    for item, url in myPageResults:
        new_page = requests.get(url).content.decode("gbk")
        dom = etree.HTML(new_page)
        new_items = dom.xpath('//tr/td/a/text()')
        new_urls = dom.xpath('//tr/td/a/@href')
        for item in new_items:
            news.append(item)
    news = random.sample(news,10)
    for new in news :
        # do bmob operation 
        piece = New(title=new)
        piece.save()
    return render_template('news.html',news=news)
'''

# 这里使用七牛云进行录音的保存，但是七牛云存在一个问题： 没有公共域名可用。
# 上传资源的下载必须使用 api 获取， 七牛的 qshell 工具的 qshell get 下载
# 下载后的文件为 silk 文件，需要进行ffmpeg转码， 参考使用 https://github.com/kn007/silk-v3-decoder 进行转码 
@app.route('/qiniu',methods=['GET','POST'])
def qiniu():
	if request.method == 'POST' :
		recordFile = request.files['file']
		key = request.form.get('filename')
		recordFile.save(os.path.join('./',key)) 
		q = Auth(os.environ['qiniuak'], os.environ['qiniusk'])
		bucket_name = 'travel'
		token = q.upload_token(bucket_name, key, 3600)
		ret, info = put_file(token, key, './'+key)
		return str(datetime.datetime.now())

@app.route('/qiniu_pic',methods=['GET','POST'])
def qiniu():
    if request.method == 'POST' :
        recordFile = request.files['file']
        key = request.form.get('filename')
        recordFile.save(os.path.join('./',key)) 
        q = Auth(os.environ['qiniuak'], os.environ['qiniusk'])
        bucket_name = 'pic'
        token = q.upload_token(bucket_name, key, 3600)
        ret, info = put_file(token, key, './'+key)
        return str(datetime.datetime.now())


@app.route('/list')
def list():
    q = Auth(os.environ['qiniuak'], os.environ['qiniusk'])
    bucket = BucketManager(q)
    bucket_name = 'travel'
    prefix = None
    limit = 200
    delimiter = None
    marker = None
    ret, eof, info = bucket.list(bucket_name, prefix, marker, limit, delimiter)
    ret_str = ''
    for i in ret['items']:
        ret_str += i['key']
        ret_str += '\n'
    return ret_str



@app.route('/words')
def words():
    url = "https://api.guoch.xyz"
    words = []
    for i in range(10,15):
        content = requests.get(url).content
        piece = New(title=content)
        piece.save()
        words.append(content)
    url = "https://sslapi.hitokoto.cn/?c=f&encode=text"
    for i in range(10,15):
        content = requests.get(url).content
        piece = New(title=content)
        piece.save()
        words.append(content)
    return render_template('news.html',news=words)


@app.route('/cz',methods=['GET','POST'])   #  检查todo应用逻辑,定期推送
def cz():
    beary_todo_url = os.environ['bearytodo']
    bmobak = os.environ['bmobak']
    bmobsk = os.environ['bmobsk']
    b = Bmob(bmobak,bmobsk)
    day_string = str(datetime.datetime.now().month)+'-'+str(datetime.datetime.now().day)
    find_content = b.find( # 查找数据库
        "today",
        where = {"day":day_string},
        keys='content' # 表名 
        ).stringData # 输出string格式的内容
    d_time = datetime.datetime.strptime(str(datetime.datetime.now().date())+'9:00', '%Y-%m-%d%H:%M')
    d_time1 =  datetime.datetime.strptime(str(datetime.datetime.now().date())+'9:30', '%Y-%m-%d%H:%M')
    n_time = datetime.datetime.now()
    if n_time > d_time and n_time < d_time1:
        payloadData = {"text":find_content}
        payloadHeader = {
            'Content-Type': 'application/json',
        }
        r=requests.post(beary_todo_url,data=json.dumps(payloadData),headers=payloadHeader)
    else:
        pass
    return str(datetime.datetime.now())  


@app.route('/borrow',methods=['GET','POST'])   # 拟债券利率核算 应用逻辑
def borrow():
    beary_check_url = os.environ['bearycheck']
    url = "https://official.gkoudai.com/officialNetworkApi/GetQuotesDetail?id=6"
    myPage = requests.get(url)
    loads = json.loads(myPage.text)
    last_close = loads['data']['quotes']['last_close']
    last_close = parseint(last_close)
    nowPrice = loads['data']['quotes']['nowPrice']
    nowPrice = parseint(nowPrice)
    basePrice1 = 4153   # 30share
    basePrice2 = 4140   # 30share
    basePrice3 = 4023   # 83share
    T1 = (nowPrice-basePrice1)/(last_close-nowPrice)
    L1 = 1800000/(T1*basePrice1)
    T2 = (nowPrice-basePrice2)/(last_close-nowPrice)
    L2 = 1800000/(T2*basePrice2)
    T3 = (nowPrice-basePrice3)/(last_close-nowPrice)
    L3 = 1800000/(T3*basePrice3)
    return_val = "实时结算：P1募集利率为: "+str(L1)+"% 募集天数为: "+str(T1)
    return_val += "实时结算：P2募集利率为: "+str(L2)+"% 募集天数为: "+str(T2)
    return_val += "实时结算：P3募集利率为: "+str(L3)+"% 募集天数为: "+str(T3)  
    d_time = datetime.datetime.strptime(str(datetime.datetime.now().date())+'16:00', '%Y-%m-%d%H:%M')
    d_time1 =  datetime.datetime.strptime(str(datetime.datetime.now().date())+'16:30', '%Y-%m-%d%H:%M')
    n_time = datetime.datetime.now()
    if n_time > d_time and n_time < d_time1:
        payloadData = {"text":return_val}
        payloadHeader = {
            'Content-Type': 'application/json'
        }
        r=requests.post(beary_check_url,data=json.dumps(payloadData),headers=payloadHeader)
    else:
        pass
    return str(datetime.datetime.now())+str(nowPrice)


@app.route('/sliver',methods=['GET','POST'])   # 常在 应用逻辑
def silver():
    url = "https://official.gkoudai.com/officialNetworkApi/GetQuotesDetail?id=6"
    myPage = requests.get(url)
    loads = json.loads(myPage.text)
    nowPrice = loads['data']['quotes']['nowPrice']
    Silver = leancloud.Object.extend('silver')
    silver_object = Silver()
    silver_object.set('price', int(nowPrice))
    silver_object.set('time', datetime.datetime.now())
    silver_object.save()
    return str(datetime.datetime.now())+str(nowPrice)

@app.route('/check',methods=['GET','POST'])   # 常在 应用逻辑
def check():
    beary_check_url = os.environ['bearycheck']
    min_level = request.args.get('level')  # 描述分钟级别
    Silver = leancloud.Object.extend('silver')
    query = Silver.query
    query.select('price')
    #query.limit(100)
    # query.descending('createdAt')
    # price_list = query.find()
    if(min_level < 1):
        min_level = 5
    else:
        min_level = str2int(min_level)
    query.greater_than_or_equal_to('time', (datetime.datetime.now()-datetime.timedelta(minutes=min_level)))
    query.add_descending('price')
    price_list = query.find()
    price_max = price_list[0].get('price') # 两分钟内最大值
    price_min= price_list[len(price_list)-1].get('price')  # 两分钟内最小值
    if((price_max-price_min)>5 or (price_max-price_min)<-5 ):
        return_val = "值得一买"
        payloadData = {"text":"值得一买"}
        payloadHeader = {
            'Content-Type': 'application/json',
        }
        r=requests.post(beary_check_url,data=json.dumps(payloadData),headers=payloadHeader)
    else:
        return_val = "不值一买"+str(price_max)+str(price_min)
        # postdata={'payload':{"text":"5分钟级别，不值一买"}}
        # r=requests.post('https://hook.bearychat.com/=bwHe6/incoming/cce0949a2d6479498e212e07f3502b84',data=postdata)
    return return_val

# 新闻类榜单
@app.route('/timedtodo',methods=['GET','POST'])   # 常在 应用逻辑
def timedtodo():
    beary_todo_url = os.environ['bearytodo']
    payloadHeader = {
        'Content-Type': 'application/json',
    }
    TimedTodo = leancloud.Object.extend('timedTodo')
    query = TimedTodo.query
    query.select('todo','delta')
    query.less_than_or_equal_to('time',datetime.datetime.now())
    todo_list = query.find()
    for todo in todo_list:
        payloadData = formpayload(todo.get('todo'))
        delta = todo.get('delta')
        r=requests.post(beary_todo_url,data=json.dumps(payloadData),headers=payloadHeader)
        todo.set('time',(datetime.datetime.now()+datetime.timedelta(days = delta)))
        todo.save()
    return str(len(todo_list))

