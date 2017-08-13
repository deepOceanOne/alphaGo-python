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
        'name' : "Around the world",
        'singer':"Aqua",
        'src' : "http://ws.stream.qqmusic.qq.com/C100000Q26PX3Xz8EP.m4a?fromtag=38",
        'poster':"http://musicdata.baidu.com/data2/pic/64166dae89016b79f97e033b7d71e174/326548014/326548014.jpg@s_0,w_180"
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



