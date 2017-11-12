# coding: utf-8

from datetime import datetime

from flask import Flask,Response
from flask import render_template
from flask import request, make_response
from flask_sockets import Sockets
from flask import redirect
import jieba

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

# for text-to-speech  
# coding=utf-8
EXAMPLE = '在文本框中输入需要进行截词的文本，系统将会返回截词后文本、截词后的语音合成.'
"""
常量,作为截词的示例文本
"""

R = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
"""
语速（语速等级从0-10）
"""

F = ['8khz_8bit_mono', '8khz_8bit_stereo', '8khz_16bit_mono', '8khz_16bit_stereo',
     '11khz_8bit_mono', '11khz_8bit_stereo', '11khz_16bit_mono', '11khz_16bit_stereo',
     '12khz_8bit_mono', '12khz_8bit_stereo', '12khz_16bit_mono', '12khz_16bit_stereo',
     '16khz_8bit_mono', '16khz_8bit_stereo', '16khz_16bit_mono', '16khz_16bit_stereo',
     '22khz_8bit_mono', '22khz_8bit_stereo', '22khz_16bit_mono', '22khz_16bit_stereo',
     '24khz_8bit_mono', '24khz_8bit_stereo', '24khz_16bit_mono', '24khz_16bit_stereo',
     '32khz_8bit_mono', '32khz_8bit_stereo', '32khz_16bit_mono', '32khz_16bit_stereo',
     '44khz_8bit_mono', '44khz_8bit_stereo', '44khz_16bit_mono', '44khz_16bit_stereo',
     '48khz_8bit_mono', '48khz_8bit_stereo', '48khz_16bit_mono', '48khz_16bit_stereo',
     'alaw_8khz_mono', 'alaw_8khz_stereo', 'alaw_11khz_mono', 'alaw_11khz_stereo',
     'alaw_22khz_mono', 'alaw_22khz_stereo', 'alaw_44khz_mono', 'alaw_44khz_stereo',
     'ulaw_8khz_mono', 'ulaw_8khz_stereo', 'ulaw_11khz_mono', 'ulaw_11khz_stereo',
     'ulaw_22khz_mono', 'ulaw_22khz_stereo', 'ulaw_44khz_mono', 'ulaw_44khz_stereo']
"""
音频格式
"""

def cut(to_cut=EXAMPLE):
    """
    对文本进行截词操作,这里文本格式为string类型
    :param to_cut:
    :return:
    """
    seg_list = jieba.cut(to_cut)
    seg = list(seg_list)
    dust_seg = ''

    for value in seg:
        dust_seg = dust_seg + value + ' : '

    return dust_seg[0:-2].encode('utf-8')


@app.route('/api/cut', methods=['GET', 'POST'])
def ajax_post_text():
    to_cut = request.form.get('text')
    return cut(to_cut)


@app.route('/api/speech', methods=['POST'])
def ajax_post_cut():
    r = request.form.get('r')
    f = request.form.get('f')
    tts_cut = request.form.get('cut-speech')

    return render_template('seg.html', r=r, f=f, R=R, F=F,
                           src=tts_cut.encode('utf-8'),
                           cut=tts_cut.encode('utf-8'))

@app.route('/')
def index():
    """
    默认处理方法
    :return:
    """
    return render_template('seg.html', r=R[0], f=F[0], R=R, F=F,
                           src=cut(EXAMPLE), cut=cut(EXAMPLE))

# end of text-to-speech

# the music push part is temporarily 
@app.route('/music')
def music():
    
    # audio src to be pushed ... 
    audio = {
        'name' : "Around the world",
        'author':"Aqua",
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



