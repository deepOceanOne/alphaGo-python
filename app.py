# coding: utf-8

from datetime import datetime

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

from Bmob import BmobSDK,BmobModel
# add for qiniu storage 
from qiniu import Auth, put_file, etag, put_stream, put_data
import qiniu.config

# define a Model 
class New(BmobModel):
    title = '' # title 

# setup BmobSDK
BmobSDK.setup(os.environ['bmobappid'],os.environ['bmobappkey'])    


# end of Bmob thing 

app = Flask(__name__)

# 动态路由
app.register_blueprint(todos_view, url_prefix='/todos')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/time')
def time():
    return str(datetime.now())

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
		return str(datetime.now())



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

# 新闻类榜单



