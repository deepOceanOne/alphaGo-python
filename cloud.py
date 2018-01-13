# coding: utf-8

from leancloud import Engine
from leancloud import LeanEngineError
import requests

engine = Engine()


@engine.define
def hello(**params):
    if 'name' in params:
        return 'Hello, {}!'.format(params['name'])
    else:
        return 'Hello, LeanCloud!'

@engine.define
def push(**params):
	url = "http://push.leanapp.cn/words"
	requests.get(url)
	return "push completed!"


@engine.before_save('Todo')
def before_todo_save(todo):
    content = todo.get('content')
    if not content:
        raise LeanEngineError('内容不能为空')
    if len(content) >= 240:
        todo.set('content', content[:240] + ' ...')
