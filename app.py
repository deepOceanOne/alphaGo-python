# coding: utf-8

from datetime import datetime

from flask import Flask,Response
from flask import render_template
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
    audio = {
        'title' : "张三的歌",
        'src' : "http://www.tingge123.com/mp3/2016-04-22/1461291711.mp3",
        'postrt':"http://musicdata.baidu.com/data2/pic/88574881/88574881.jpg@s_0,w_180"
    }
    return Response(json.dumps(audio), mimetype='application/json')




