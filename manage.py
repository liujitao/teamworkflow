# -*- coding: utf-8 -*-                                                                                                                               

from flask.ext.script import Manager, Server, prompt_bool
from app import db, app
from app.models import User

manager = Manager(app)
manager.add_command('runserver', Server(host='0.0.0.0', use_debugger=True))

@manager.command
def create_tables():
    db.create_all()

@manager.command
def initial_tables():
    db.session.add_all([ \
        User(name=u'管理员', email=u'admin@tvmining.com', qq='', mobile='', password='admin', team_id=1, active=1),
    ])

    db.session.commit() 

@manager.command
def drop_tables():
	if prompt_bool(u'你确认要删除所有数据?删除执行后数据不可恢复!'):
		db.drop_all()

if __name__ == '__main__':
    manager.run() 
