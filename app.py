# coding: utf-8

from datetime import datetime

from flask import Flask,Response
from flask import render_template
from flask import request, make_response
from flask_sockets import Sockets

from views.todos import todos_view

import os
import sys
import urllib2
import requests
import re
from lxml import etree
import json 

app = Flask(__name__)

# 动态路由
app.register_blueprint(todos_view, url_prefix='/todos')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/time')
def time():
    return str(datetime.now())

@app.route('/music')
def music():
    
    # audio src to be pushed ... 
    audio = {
        'name' : "张三的歌",
        'author':"张子石",
        'src' : "http://www.tingge123.com/mp3/2016-04-22/1461291711.mp3",
        'poster':"http://musicdata.baidu.com/data2/pic/88574881/88574881.jpg@s_0,w_180"
    }
    return Response(json.dumps(audio), mimetype='application/json')

@app.route('/search')
def search():
    import urllib
    url_string = request.url.split("url=")[1] # Hackish; but works if the requested URL contains query params
    print 'url string is : '+urllib.unquote(url_string)
    try:
        page = urllib.urlopen(urllib.unquote(url_string))
        html = page.read()
        return html
    except Exception, e :
        return e 



