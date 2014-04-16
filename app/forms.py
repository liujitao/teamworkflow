# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, BooleanField, TextAreaField, SelectField
from wtforms.validators import Required, EqualTo, Email

from models import User

class WorkLogEditForm(Form):
	title = TextField(u'标题')
	content_a = TextAreaField(u'服务器运行状态')
	content_b = TextAreaField(u'直播流&采集')
	content_c = TextAreaField(u'北美SunTV')
	content_d = TextAreaField(u'监控服务器变更')
	content_e = TextAreaField(u'其他')

class WikiEditForm(Form):
	title = TextField(u'标题')
	content = TextAreaField(u'内容')
	category_id = SelectField(u'类别', coerce=int)

class UserEditForm(Form):
	name = TextField(u'中文姓名', [Required(u'请输入中文姓名')])
	email = TextField(u'邮件地址', [Required(u'请输入邮件地址')])
	qq = TextField(u'QQ号码')
	mobile = TextField(u'移动电话')
	password = TextField(u'用户密码')
	team_id = SelectField(u'所属团队', coerce=int)
	# 扩展验证 wtform

class LoginForm(Form):
    email = TextField("email", [Required(u'请输入邮件地址')])
    password = PasswordField('Password', [Required(u'请输入登录密码')])

class CaptureEditForm(Form):
	location_id = SelectField(u'IDC位置', coerce=int)
	model_id = SelectField(u'设备型号', coerce=int)
	idc_sn = TextField(u'IDC SN')
	hostname = TextField(u'主机名')
	nic1 = TextField(u'外网')
	nic2 = TextField(u'内网')
	nic3 = TextField(u'内网(组播)')
	category = TextField(u'用途')
	password = TextField(u'登录密码')
	channel = TextField(u'采集频道')
	capture_method = TextField(u'采集方式')
	content = TextAreaField(u'备注')