# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

app = Flask(__name__)
app.config.from_object('app.config')

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

#login_manager.login_view = 'login'

# 注册filters
def split(value):
    results = []
    for channel in value.split('|'):
        if channel != '':
            en, cn, flag = channel.split(':') 
            results.append(cn+u':'+en+u'<b>[主]</b>') if flag == '1' else results.append(cn+u':'+en+u'<b>[备]</b>')
        else:
            results = ''

    return ' '.join(results) if results != '' else ''

env=app.jinja_env  
env.filters['split'] = split

from app import models
from app import views
