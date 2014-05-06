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
	active = db.Column(db.Integer, default=1) # 0锁定 1激活  

	def __init__(self, name, email, qq, mobile, password, team_id, active):
		self.name = name
		self.email = email.lower()	
		self.qq = qq
		self.mobile = mobile
		self.set_password(password)
		self.team_id = team_id
		self.active = active

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
		if self.active == 1:
			return True
		else:
			return False

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
	category_id = db.Column(db.Integer, default=1)
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
	user_id = db.Column(db.Integer) # 用户id
	name = db.Column(db.String(40))
	year = db.Column(db.Integer)
	month = db.Column(db.Integer)
	days = db.Column(db.Integer)
	type = db.Column(db.Integer) # 1轮班 2替班 3正常班
	list = db.Column(db.String(100)) # 每天值班标识, 0正常休, 1早班, 2晚班, 3全班(早+晚), 25调休
	morning = db.Column(db.Integer) # 早班数
	evening = db.Column(db.Integer) # 晚班数
	rest = db.Column(db.Integer) # 调休数
	overtime = db.Column(db.Integer) # 加班时长
	updated_user = db.Column(db.String(40), default='admin')
	updated_time = db.Column(db.DateTime, default=datetime.datetime.now())
	updated_count = db.Column(db.Integer)

class Task(db.Model):
	__tablename__ = 'task'
	id = db.Column(db.Integer, primary_key=True, index=True)
	title = db.Column(db.String(40))
	name = db.Column(db.String(40))
	team = db.Column(db.String(40))
	mobile = db.Column(db.String(40))
	email = db.Column(db.String(40))
	planned_time = db.Column(db.DateTime) # 计划完成时间
	type = db.Column(db.Integer) # 1申请资源 2回收资源 3日常检查 4故障处理
	hardware = db.Column(db.Text) # 虚拟机实体机,内存,硬盘,存储空间
	network = db.Column(db.Text) # 访问互联网, 开通外网访问, 内网访问权限
	storage = db.Column(db.Text) # 挂载公共存储数据 
	domain = db.Column(db.Text) # 内网域名, 外网域名
	expired_time = db.Column(db.DateTime) # 月转化为天
	recycle = db.Column(db.Text) # 回收资源
	handle = db.Column(db.Text) # 故障处理&运维部署
	created_user = db.Column(db.String(40), default='admin') # 建立人员
	created_time = db.Column(db.DateTime, default=datetime.datetime.now())
	assigned_user = db.Column(db.String(40)) # 派单人
	assigned_time = db.Column(db.DateTime)
	execute = db.Column(db.Text) # 工单执行结果
	executed_user_id = db.Column(db.String(40)) # 执行人员id 1,2,3
	executed_user = db.Column(db.String(40)) # 执行人员
	executed_commit_user = db.Column(db.String(40)) # 执行结果提交人
	executed_time = db.Column(db.DateTime) # 执行完成时间
	audit = db.Column(db.Text) # 工单审核结果
	audited_user = db.Column(db.String(40)) # 审核人
	audited_time = db.Column(db.DateTime) # 审核完成时间
	expire = db.Column(db.Integer, default=0) # 过期状态, 0未过期, 1过期
	link = db.Column(db.Integer, default=0) # 资源回收, 关联资源申请id 
	status = db.Column(db.Integer) # 工单状态, 1已生成(未指派) 2已指派(未执行) 3已执行(未审核) 4已审核 5已回收

class YumSite(db.Model):
	__tablename__ = 'yum_site'
	id = db.Column(db.Integer, primary_key=True, index=True)
	repository_id = db.Column(db.Integer) # 1 centos 2 epel 3 repoforge
	country = db.Column(db.String(40))
	name = db.Column(db.String(40), nullable=False)
	http = db.Column(db.String(40))
	rsync = db.Column(db.String(40), nullable=False)
	speed = db.Column(db.String(40), default='0')
	updated_user = db.Column(db.String(40), default='admin')
	updated_time = db.Column(db.DateTime, default=datetime.datetime.now())
