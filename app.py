# coding: utf-8

from datetime import datetime

from flask import Flask
from flask import render_template
from flask_sockets import Sockets

from views.todos import todos_view

import os
import sys
import urllib2
import requests
import re
from lxml import etree

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
            item = item.encode("utf-8")
            news.append(item)
    return render_template('news.html',news=news)


