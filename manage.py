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
		User(name=u'管理员', email=u'admin@tvmining.com', qq='', mobile='', password='admin'),
		User(name=u'张剑锋', email=u'zhangjianfeng@tvmining.com', qq='100000', mobile='1300000001', password='admin'),
		User(name=u'李俊', email=u'lijun@tvmining.com', qq='200000', mobile='1300000002', password='123456'),
		User(name=u'董雪停', email=u'dongxueting@tvmining.com', qq='300000', mobile='1300000003', password='123456'),
		User(name=u'张振祥', email=u'zhangzhenxiang@tvmining.com', qq='400000', mobile='1300000004', password='123456'),
		User(name=u'张喜江', email=u'zhangxijiang@tvmining.com', qq='500000', mobile='1300000005', password='123456'),
		User(name=u'王锡武', email=u'wangxiwu@tvmining.com', qq='600000', mobile='1300000006', password='123456'),
		User(name=u'王素', email=u'wangsu@tvmining.com', qq='700000', mobile='1300000007', password='123456'),
		User(name=u'黎宇', email=u'liyu@tvmining.com', qq='800000', mobile='1300000008', password='123456'),		
		User(name=u'吴波', email=u'wubo@tvmining.com', qq='900000', mobile='1300000009', password='123456'),
		User(name=u'史训训', email=u'shixunxun@tvmining.com', qq='1000000', mobile='1300000010', password='123456'),
		User(name=u'刘继涛', email=u'liujitao@tvmining.com', qq='1100000', mobile='1300000011', password='123456'),	
		User(name=u'王中元', email=u'wangzhongyuan@tvmining.com', qq='1200000', mobile='1300000012', password='123456'),
		User(name=u'樊占涛', email=u'fanzhantao@tvmining.com', qq='1300000', mobile='1300000013', password='123456'),
		User(name=u'刑磊', email=u'xinglei@tvmining.com', qq='1400000', mobile='1300000014', password='123456'),
		User(name=u'童佩', email=u'tongpei@tvmining.com', qq='1500000', mobile='1300000015', password='123456'),
		User(name=u'黄宇飞', email=u'huangyufei@tvmining.com', qq='1600000', mobile='1300000016', password='123456'),
		User(name=u'郭启明', email=u'guoqiming@tvmining.com', qq='1300000', mobile='1300000013', password='123456'),
		User(name=u'杨昆', email=u'yangkun@tvmining.com', qq='1400000', mobile='1300000014', password='123456'),
		User(name=u'李月强', email=u'liyueqiang@tvmining.com', qq='1500000', mobile='1300000015', password='123456'),
		User(name=u'陆晶', email=u'lujing@tvmining.com', qq='1600000', mobile='1300000016', password='123456'),
		User(name=u'赵飞鲁', email=u'zhaofeilu@tvmining.com', qq='1400000', mobile='1300000014', password='123456'),
		User(name=u'于江', email=u'yujiang@tvmining.com', qq='1500000', mobile='1300000015', password='123456'),
		User(name=u'aaa', email=u'huangyufei@tvmining.com', qq='1600000', mobile='1300000016', password='123456'),
	])

	db.session.commit() 

@manager.command
def drop_tables():
	if prompt_bool(u'你确认要删除所有数据?删除执行后数据不可恢复!'):
		db.drop_all()

if __name__ == '__main__':
    manager.run() 
