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
from urllib.request import urlopen
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
# 用于随机数产生
import random

# 用于百度文字识别
from aip import AipOcr
# 用于网页内容提取
from goose3 import Goose 
from goose3.text import StopWordsChinese


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


def parseint(string):
    return int(''.join([x for x in string if x.isdigit()]))

def formpayload(content):
    payloadData = {"text":content}
    return payloadData

# 加入百度翻译的api，但是这是个python2版本，这里没法用，以后试试升级成python3版本，百度的API服务确实过于陈旧了
def any2chn_baidu(_appid,_secretKey,_q):
    appid = _appid #你的appid
    secretKey = _secretKey #你的密钥
    httpClient = None
    myurl = '/api/trans/vip/translate'
    q = _q
    fromLang = 'auto'
    toLang = 'zh'
    salt = random.randint(32768, 65536)
    sign = appid+q+str(salt)+secretKey
    m1 = md5.new()
    m1.update(sign)
    sign = m1.hexdigest()
    myurl = myurl+'?appid='+appid+'&q='+urllib.quote(q)+'&from='+fromLang+'&to='+toLang+'&salt='+str(salt)+'&sign='+sign
    httpClient = httplib.HTTPConnection('api.fanyi.baidu.com')
    httpClient.request('GET', myurl)
    #response是HTTPResponse对象
    response = httpClient.getresponse()
    _response = response.read()
    _response.decode('utf-8')
    _json = json.loads(_response)
    return _json['trans_result'][0]['dst'] 

# 加入有道翻译的api
def any2chn_youdao(_APP_KEY,_APP_SECRET,_q):
    APP_KEY = _APP_KEY
    APP_SECRET = _APP_SECRET
    q = _q
    data = {}
    data['from'] = 'auto'
    data['to'] = 'zh-CHS'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    size = len(q)
    q_truncate = ''
    if size <= 20 :
        q_truncate = q
    else :
        q_truncate = q[0:10] + str(size) + q[size - 10:size]
    signStr = APP_KEY + q_truncate + salt + curtime + APP_SECRET
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    sign = hash_algorithm.hexdigest()
    data['appKey'] = APP_KEY
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post('https://openapi.youdao.com/api', data=data, headers=headers)
    _response = json.loads(response.content)
    return str(_response['translation'])


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


@app.route('/postwrite',methods=['GET','POST'])   # 接收从倍洽外部post过来的消息，触发词为“POST”
def postwrite():
		if request.method == 'POST' :
			if request.content_type.startswith('application/json'):
				data = request.get_data()
				data = json.loads(data)
			else:
				for key, value in request.form.items():
					if key.endswith('[]'):
						data[key[:-2]] = request.form.getlist(key)
					else:
						data[key] = value
		text_content = data['text']
		Writings = leancloud.Object.extend('Writings')
		writing = Writings()
		writing.set('content',text_content)
		writing.save()
		return str(datetime.datetime.now())

## 文章索引功能
@app.route('/postread',methods=['GET','POST'])   # 接收从倍洽外部post过来的消息，触发词为“POST”
def postread():
        if request.method == 'POST' :
            data = {}
            if request.content_type.startswith('application/json'):
                data = request.get_data()
                data = json.loads(data)
            else:
                for key, value in request.form.items():
                    if key.endswith('[]'):
                        data[key[:-2]] = request.form.getlist(key)
                    else:
                        data[key] = value
            return_data = {}
            tmp_str = data['text']
            url = tmp_str.replace('http ','http')
            g = Goose({'stopwords_class':StopWordsChinese})
            article = g.extract(url=url)
            text_content = article.cleaned_text
            if len(text_content)==0 :
                return_data['text'] = '未获得内容'
            else:
                Readings = leancloud.Object.extend('Readings')
                Reading = Readings()
                Reading.set('content',text_content)
                Reading.save()
                # 增加返回确认内容功能
                return_data['text'] = text_content
        return json.dumps(return_data)



# 加入搜索功能
@app.route('/postsearch',methods=['GET','POST'])   # 接收从倍洽外部post过来的消息，触发词为“POST”
def postsearch():
        if request.method == 'POST' :
            if request.content_type.startswith('application/json'):
                data = request.get_data()
                data = json.loads(data)
            else:
                for key, value in request.form.items():
                    if key.endswith('[]'):
                        data[key[:-2]] = request.form.getlist(key)
                    else:
                        data[key] = value
        return_data = {} 
        return_data['text'] = text_content
        return json.dumps(return_data)


# 文字助手，增加一个图片解析文字的功能，使用 leancloud、bmob以及百度云的智能解析。
@app.route('/text',methods=['GET','POST'])
def text():
    if request.method == 'POST' :
        addr = request.form["addr"]
        time = request.form["time"]
        XXQG = leancloud.Object.extend('xxqg')
        xxqg = XXQG()
        xxqg.set('time',time)
        xxqg.set('addr',addr)
        xxqg.save()
        return str(datetime.datetime.now())


 # 解析助手，百度云的文字识别。
@app.route('/extract',methods=['GET','POST'])
def extract():
    beary_text_url = os.environ['bearytext']
    YOUDAO_APP_KEY = os.environ['YOUDAO_APP_KEY']
    YOUDAO_APP_SECRET = os.environ['YOUDAO_APP_SECRET']
    APP_ID = os.environ['baidu_id']
    API_KEY = os.environ['baidu_ak']
    SECRET_KEY = os.environ['baidu_sk']
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    options = {}
    options["language_type"] = "CHN_ENG"
    options["detect_direction"] = "false"
    options["detect_language"] = "true"
    options["probability"] = "false"
    payloadHeader = {
        'Content-Type': 'application/json',
    }
    #  查询最近产生的识别订单，进行集中统一识别
    XXQG = leancloud.Object.extend('xxqg')
    query = XXQG.query
    query.select('addr')
    query.greater_than_or_equal_to('createdAt', (datetime.datetime.now()-datetime.timedelta(minutes=7)))
    xxqg_list = query.find()
    for xxqg in xxqg_list:
        url = xxqg.get('addr')
        text = client.basicGeneralUrl(url,options)
        words_result = text["words_result"]
        words_result_return = ''
        words_result_return_posfix = 'POST '
        for word in words_result:
            words_result_return+=word["words"]    
        # 加入翻译内容,使用有道翻译引擎
        if '的' in words_result_return:  # 基本可以判断这是一段中文内容
            tmp_dump = 1
        else :  #这段需要翻译一下
            words_result_return = any2chn_youdao(YOUDAO_APP_KEY,YOUDAO_APP_SECRET,words_result_return)
        words_result_return = words_result_return_posfix + words_result_return
        payloadData = formpayload(words_result_return)
        r=requests.post(beary_text_url,data=json.dumps(payloadData),headers=payloadHeader)
        xxqg.destroy()
    return str(datetime.datetime.now())     


@app.route('/qiniu_pic',methods=['GET','POST'])
def qiniu_pic():
    if request.method == 'POST' :
        recordFile = request.files['file']
        key = request.form.get('filename')
        recordFile.save(os.path.join('./',key)) 
        q = Auth(os.environ['qiniuak'], os.environ['qiniusk'])
        bucket_name = 'pic'
        token = q.upload_token(bucket_name, key, 3600)
        ret, info = put_file(token, key, './'+key)
        return str(datetime.datetime.now())


@app.route('/baby',methods=['GET','POST'])    # 文字解析和索引服务
def baby():
    beary_baby_url = os.environ['bearybaby']
    babypicbase = os.environ['babypicbase']
    d_time = datetime.datetime.strptime(str(datetime.datetime.now().date())+'11:30', '%Y-%m-%d%H:%M')
    d_time1 =  datetime.datetime.strptime(str(datetime.datetime.now().date())+'12:30', '%Y-%m-%d%H:%M')
    n_time = datetime.datetime.now()
    Baby = leancloud.Object.extend('baby')
    query = Baby.query
    query.select('addr')
    count = query.count()
    if count > 1 and n_time > d_time and n_time < d_time1:   #进行图片推送
        first_result = query.first()
        pic_addr = first_result.get('addr')
        first_result.destroy()
        payloadData = {"text":"每日一图","channel": "Baby","attachments": [{"images": [{"url":babypicbase+pic_addr}]}]}
        payloadHeader = {
            'Content-Type': 'application/json',
        }
        r=requests.post(beary_baby_url,data=json.dumps(payloadData),headers=payloadHeader)
    else:
        pass
    return str(datetime.datetime.now())


@app.route('/fulltext',methods=['GET','POST'])    # 文字解析和索引服务
def fulltext():
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


## 之前用于todaypro的新闻推送服务,已废弃
'''
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
'''


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
    basePrice1 = 4138   # 5share
    basePrice2 = 4138   # 5share
    basePrice3 = 4023   # 83share
    T1 = (nowPrice-basePrice1)/(last_close-nowPrice)
    L1 = 1800000/(T1*basePrice1)
    M1 = basePrice1*5   
    T2 = (nowPrice-basePrice2)/(last_close-nowPrice)
    L2 = 1800000/(T2*basePrice2)
    M2 = basePrice2*5 
    T3 = (nowPrice-basePrice3)/(last_close-nowPrice)
    L3 = 1800000/(T3*basePrice3)
    M3 = basePrice3*83
    return_val = "实时结算：P1募集利率为: "+str(L1)+"% 募集天数为: "+str(T1)+" 募集总额为: "+str(M1)
    return_val += "实时结算：P2募集利率为: "+str(L2)+"% 募集天数为: "+str(T2)+" 募集总额为: "+str(M2)
    return_val += "实时结算：P3募集利率为: "+str(L3)+"% 募集天数为: "+str(T3)+" 募集总额为: "+str(M3)  
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
    min_level = request.args.get('level') # 描述分钟级别
    Silver = leancloud.Object.extend('silver')
    query = Silver.query
    query.select('price')
    #query.limit(100)
    # query.descending('createdAt')
    # price_list = query.find()
    min_level = parseint(min_level)
    if(min_level < 1):
        min_level = 5
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

