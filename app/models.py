	# -*- coding: utf-8 -*-

from werkzeug.security import generate_password_hash, check_password_hash
import datetime

from app import db

class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True, index=True)
	name = db.Column(db.String(40))
	email = db.Column(db.String(40), unique=True)
	qq = db.Column(db.String(40), unique=True)
	mobile = db.Column(db.String(40), unique=True)
	pwdhash = db.Column(db.String(40))
	team_id = db.Column(db.Integer, default=1) # 1管理 2机房运维 3采集 4网络存储

	def __init__(self, name, email, qq, mobile, password, team_id):
		self.name = name
		self.email = email.lower()	
		self.qq = qq
		self.mobile = mobile
		self.set_password(password)
		self.team_id = team_id

	def __repr__(self):
		return '<User %r>' % (self.name)

	def set_password(self, password):
		self.pwdhash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.pwdhash, password)

# flask-login 
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)

class WorkLog(db.Model):
	__tablename__ = 'work_log'
	id = db.Column(db.Integer, primary_key=True, index=True)
	title = db.Column(db.String(100))
	content_a = db.Column(db.Text)
	content_b = db.Column(db.Text)
	content_c = db.Column(db.Text)
	content_d = db.Column(db.Text)
	content_e = db.Column(db.Text)
	created_user = db.Column(db.String(40), default='admin')
	created_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_user = db.Column(db.String(40), default='admin')
	updated_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_count = db.Column(db.Integer)

class Wiki(db.Model):
	__tablename__ = 'wiki'
	id = db.Column(db.Integer, primary_key=True, index=True)
	title = db.Column(db.String(100))
	content = db.Column(db.Text)
	category_id = db.Column(db.Integer)
	created_user = db.Column(db.String(40), default='admin')
	created_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_user = db.Column(db.String(40), default='admin')
	updated_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_count = db.Column(db.Integer)

class Capture(db.Model):
	__tablename__ = 'capture'
	id = db.Column(db.Integer, primary_key=True, index=True)
	location_id = db.Column(db.Integer)
	idc_sn = db.Column(db.String(40))
	hostname = db.Column(db.String(40), unique=True)
	model_id = db.Column(db.Integer, default=0) # 1r410 2r710 3双子星 4超微双子星 5r420 6r720
	nic1 = db.Column(db.String(40))
	nic2 = db.Column(db.String(40))
	nic3 = db.Column(db.String(40))
	category = db.Column(db.String(40))
	password = db.Column(db.String(40))
	channel = db.Column(db.String(40))
	capture_method = db.Column(db.String(40))
	content = db.Column(db.Text)
	created_user = db.Column(db.String(40), default='admin')
	created_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_user = db.Column(db.String(40), default='admin')
	updated_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_count = db.Column(db.Integer)

class Schedule(db.Model):
	__tablename__ = 'schedule'
	id = db.Column(db.Integer, primary_key=True, index=True)
	order_id = db.Column(db.Integer) # 值班人员id，从1开始
	name = db.Column(db.String(40))
	year = db.Column(db.Integer)
	month = db.Column(db.Integer)
	days = db.Column(db.Integer)
	type = db.Column(db.Integer) # 1轮班 2替班
	list = db.Column(db.String(100)) # 每天值班标识, 0正常休, 1早班,  2晚班, 3换班, 4调休, 5早晚全班
	morning = db.Column(db.Integer) # 计划早班数
	evening = db.Column(db.Integer) # 计划晚班数
	morning_r = db.Column(db.Integer) # 真实早班数
	evening_r = db.Column(db.Integer) # 真实晚班数
	content =db.Column(db.Text)
	updated_user = db.Column(db.String(40), default='admin')
	updated_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_count = db.Column(db.Integer)