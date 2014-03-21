	# -*- coding: utf-8 -*-

import datetime, os
from dateutil.rrule import *
	
from flask import render_template, redirect, url_for, request, jsonify, session, g
from flask.ext.sqlalchemy import Pagination
from flask.ext.login import login_user, logout_user, current_user, login_required

from models import WorkLog, Wiki, User, Capture, Schedule
from forms import WorkLogEditForm, UserEditForm, WikiEditForm, CaptureEditForm, LoginForm
from app import app, db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
	form = LoginForm(request.form)

	if form.validate_on_submit():
		user = User.query.filter_by(email=request.form['email']).first()
		if user and user.check_password(request.form['password']):
			login_user(user)
			return redirect(url_for('worklog_list'))

	return render_template('login.html', form=form)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login')) 

@app.route('/worklog/', methods=['GET'])
@app.route('/worklog/<int:page>/', methods=['GET', 'POST'])
def worklog_list(page=1):
	record_per_page = app.config['RECORD_PER_PAGE']
	pagination = WorkLog.query.order_by(WorkLog.id.desc()).paginate(page, record_per_page, False)
	worklogs = pagination.items
	return render_template('worklog_list.html', pagination=pagination, record_per_page=record_per_page, \
		worklogs=worklogs)

@app.route('/worklog/add/', methods=['GET', 'POST'])
@login_required
def worklog_add():
	form = WorkLogEditForm(request.form)

	if form.validate_on_submit():
		worklog = WorkLog()
		form.populate_obj(worklog)
		worklog.created_user = current_user.name
		worklog.updated_user = current_user.name
		worklog.updated_count = 0
		db.session.add(worklog)
		db.session.commit()
		return redirect(url_for('worklog_list'))

	return render_template('worklog_edit.html', form=form)

@app.route('/worklog/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def worklog_edit(id):
	worklog = WorkLog.query.filter(WorkLog.id==id).first()
	form = WorkLogEditForm(request.form, worklog)

	if form.validate_on_submit():
		form.populate_obj(worklog)
		worklog.updated_user = current_user.name
		worklog.updated_time = datetime.datetime.now()
		worklog.updated_count += 1
		db.session.commit()
		return redirect(url_for('worklog_list'))

	return render_template('worklog_edit.html', form=form)

@app.route('/worklog/detail/<int:id>/', methods=['GET'])
def worklog_detail(id):
	worklog = WorkLog.query.filter(WorkLog.id==id).first()
	return render_template('worklog_detail.html', worklog=worklog)

@app.route('/user/', methods=['GET'])
def user_list():
	users = User.query.order_by(User.id).all()
	return render_template('user_list.html', users=users)

@app.route('/user/add/', methods=['GET', 'POST'])
@login_required
def user_add():
	form = UserEditForm(request.form)

	if form.validate_on_submit():
		user = User(form.name.data, form.email.data, form.qq.data, form.mobile.data, form.password.data)
		db.session.add(user)
		db.session.commit()
		return redirect(url_for('user_list'))

	return render_template('user_edit.html', form=form)

@app.route('/user/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def user_edit(id):
	user = User.query.filter(User.id==id).first()
	form = UserEditForm(request.form, user)

	if form.validate_on_submit():
		form.populate_obj(user)
		if form.password.data is None:
			user.password = current_user.password
		db.session.commit()
		return redirect(url_for('user_list'))

	return render_template('user_edit.html', form=form)

@login_required
def allowed_file(filename):
    return '.' in filename and \
    	filename.rsplit('.', 1)[1] in app.config['UPLOAD_ALLOWED_EXTENSIONS']

@app.route('/upload/', methods=['GET', 'POST'])
@login_required
def file_upload():
	upload_dir = os.path.join(app.config['APP_ROOT'], app.config['UPLOAD_FOLDER'])
	max_size = app.config['UPLOAD_MAX_SIZE']
	current_date = datetime.datetime.now().strftime("%Y%m")
	save_dir = os.path.join(upload_dir, current_date) # 文件存储目录

	if not os.path.exists(save_dir):
		os.mkdir(save_dir)

	if request.method == 'POST':
		file = request.files['imgFile']

		if file and allowed_file(file.filename):
			file.save(os.path.join(save_dir, file.filename))
			save_url = request.url_root + os.path.join(app.config['UPLOAD_FOLDER'], current_date, file.filename)
			return jsonify(error=0, url=save_url)


@app.route('/wiki/', methods=['GET'])
@app.route('/wiki/<int:page>/', methods=['GET', 'POST'])
def wiki_list(page=1):
	record_per_page = app.config['RECORD_PER_PAGE']
	pagination = Wiki.query.order_by(Wiki.id.desc()).paginate(page, record_per_page, False)
	wikis = pagination.items
	return render_template('wiki_list.html', pagination=pagination, record_per_page=record_per_page, \
		wikis=wikis)

@app.route('/wiki/add/', methods=['GET', 'POST'])
@login_required
def wiki_add():
	form = WikiEditForm(request.form)
	form.category_id.choices = [(1, u'采集&直播流'), (2, u'监控系统'), (3, u'北美SunTV'), (4, u'iSearch'), (5, u'其他')]
	form.category_id.choices.insert(0, (0, u'- 指定类别 -'))

	if form.validate_on_submit():
		wiki = Wiki()
		form.populate_obj(wiki)
		wiki.created_user = current_user.name
		wiki.updated_user = current_user.name
		wiki.updated_count = 0
		db.session.add(wiki)
		db.session.commit()
		return redirect(url_for('wiki_list'))

	return render_template('wiki_edit.html', form=form)

@app.route('/wiki/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def wiki_edit(id):
	wiki = Wiki.query.filter(Wiki.id==id).first()
	form = WikiEditForm(request.form, wiki)
	form.category_id.choices = [(1, u'采集/直播流'), (2, u'监控系统'), (3, u'北美SunTV'), (4, u'iSearch'), (5, u'其他')]
	form.category_id.choices.insert(0, (0, u'- 指定类别 -'))

	if form.validate_on_submit():
		form.populate_obj(wiki)
		wiki.updated_user = current_user.name
		wiki.updated_time = datetime.datetime.now()
		wiki.updated_count += 1
		db.session.commit()
		return redirect(url_for('wiki_list'))
	return render_template('wiki_edit.html', form=form)

@app.route('/wiki/detail/<int:id>/', methods=['GET'])
def wiki_detail(id):
	wiki = Wiki.query.filter(Wiki.id==id).first()
	return render_template('wiki_detail.html', wiki=wiki)

@app.route('/capture/', methods=['GET'])
@app.route('/capture/<int:page>/', methods=['GET', 'POST'])
@login_required
def capture_list(page=1):
	record_per_page = app.config['RECORD_PER_PAGE']
	pagination = Capture.query.order_by(Capture.location_id, Capture.id).paginate(page, record_per_page, False)
	captures = pagination.items
	return render_template('capture_list.html', pagination=pagination, record_per_page=record_per_page, \
		captures=captures)

@app.route('/capture/add/', methods=['GET', 'POST'])
@login_required
def capture_add():
	form = CaptureEditForm(request.form)
	form.location_id.choices = [(1, u'无锡新区'), (2, u'无锡国际'), (3, u'北京'), (4, u'北京备份'), \
		(5, u'上海'), (6, u'上海备份'), (7, u'广州'), (8, u'长沙'), (9, u'安徽'), (10, u'山西')]
	form.location_id.choices.insert(0, (0, u'- 指定位置 -'))

	if form.validate_on_submit():
		capture = Capture()
		form.populate_obj(capture)
		capture.created_user = current_user.name
		capture.updated_user = current_user.name
		capture.updated_count = 0
		db.session.add(capture)
		db.session.commit()
		return redirect(url_for('capture_list'))

	return render_template('capture_edit.html', form=form)

@app.route('/capture/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def capture_edit(id):
	capture = Capture.query.filter(Capture.id==id).first()
	form = CaptureEditForm(request.form, capture)
	form.location_id.choices = [(1, u'无锡新区'), (2, u'无锡国际'), (3, u'北京'), (4, u'北京备份'), \
		(5, u'上海'), (6, u'上海备份'), (7, u'广州'), (8, u'长沙'), (9, u'安徽'), (10, u'山西')]
	form.location_id.choices.insert(0, (0, u'- 指定位置 -'))

	if form.validate_on_submit():
		form.populate_obj(capture)
		capture.updated_user = current_user.name
		capture.updated_time = datetime.datetime.now()
		capture.updated_count += 1
		db.session.commit()
		return redirect(url_for('capture_list'))

	return render_template('capture_edit.html', form=form)

@app.route('/capture/detail/<int:id>', methods=['GET'])
@login_required
def capture_detail(id):
	capture = Capture.query.filter(Capture.id==id).first()
	return render_template('capture_detail.html', capture=capture)

@app.route('/json/date/first_4days/', methods=['GET', 'POST'])
@login_required
def get_first_4days():
	'''
		获取前4天日期
	'''
	year = request.args.get('year', type=int)
	month = request.args.get('month', type=int)
	if month == 1:
		days = [ datetime.date(2014, 12, 25) + datetime.timedelta(days=i) for i in xrange(1, 5) ]
	else:
		days = [ datetime.date(2014, month-1, 25) + datetime.timedelta(days=i) for i in xrange(1, 5) ]

	result  = [ {'name': str(day.month) + '-' + str(day.day) } for day in days ]
	return jsonify(json=result)

@app.route('/json/schedule/init_commit/', methods=['GET', 'POST'])
@login_required
def schedule_init_commit():
	#print request.json['year'], request.json['month'], request.json['staff']
	year = request.json['year']
	month = request.json['month']
	yesterday = datetime.date(int(year), int(month), 1) - datetime.timedelta(days=1)
	last_month = yesterday.month
	start = datetime.date(int(year), int(last_month), 26)
	end = datetime.date(int(year), int(month), 25)
	days = rrule(DAILY, dtstart=start, until=end).count()	 # year/last_month/26 - year/month/25
	
	'''
	staff [u'1,张三,2-26,1', u'2,李四,2-26,1', u'3,王五,2-27,1', u'4,候六,2-27,1',  u'5,孟七,,2']
	'''

	# 排班处理
	separator = ','
	for staff in request.json['staff']:
		schedule = Schedule()
		id, name, start_date, type = staff.split(',')
		day = [0 for i in xrange(1, days+1)] # 数组初值0，代表全月休息

		if int(type) == 1:
			start_date_m, start_date_d = start_date.split('-')
			start_date_id = rrule(DAILY, dtstart=start, \
				until=datetime.date(int(year), int(start_date_m), int(start_date_d))).count()
		
			# 排班算法,4人2班,对4求余
			if start_date_id == 1:
				for i in xrange(1, days+1):
					day[i-1] = (i % 4) if (i % 4) in [1, 2] else 0
			elif start_date_id == 2:
				for i in xrange(1, days+1):
					day[i-1] = ((i - 1) % 4) if ((i - 1) % 4) in [1, 2] else 0
			elif start_date_id == 3:
				for i in xrange(2, days+1):
					day[i-1] = ((i - 2) % 4) if ((i - 2) % 4) in [1, 2] else 0
			elif start_date_id == 4:
				day[0] = 2
				for i in xrange(3, days+1):
					day[i-1] = ((i - 3) % 4) if ((i - 3) % 4) in [1, 2] else 0

		#保存数据库
		schedule.name = name	
		schedule.year = year
		schedule.month = month
		schedule.days = days
		schedule.type = type
		schedule.list = separator.join([str(i) for i in day])
		schedule.morning =  0 if len([i for i in day if i == 1]) == 0 else len([i for i in day if i == 1]) - 1
 		schedule.evening = len([i for i in day if i == 2])
 		schedule.morning_r = 0 if len([i for i in day if i == 1]) == 0 else len([i for i in day if i == 1])
 		schedule.evening_r = len([i for i in day if i == 2])
		schedule.created_user = current_user.name
		schedule.updated_user = current_user.name
		schedule.updated_count = 0

		db.session.add(schedule)
	
	db.session.commit()

	return jsonify(json=True)

@app.route('/json/schedule/edit_commit/', methods=['GET', 'POST'])
@login_required
def schedule_edit_commit():
	#print request.json['year'], request.json['month'], request.json['staff']
	'''
	staff [
		{'id': 1, 'list': '1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0'},
		{'id': 2, 'list': '1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0'},
		{'id': 3, 'list': '1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0'},
		...
	]
	'''

	for staff in request.json['staff']:
		schedule = Schedule.query.filter(Schedule.year==request.json['year'], \
			Schedule.month==request.json['month'], Schedule.id==int(staff['id'])).first()

		schedule.list = staff['list']
		schedule.morning_r = 0 if len([i for i in staff['list'].split(',') if i in ['1', '5']]) == 0 \
			else len([i for i in staff['list'].split(',') if i in ['1', '5']])
 		schedule.evening_r = len([i for i in staff['list'].split(',') if i in ['2', '5']])
 		schedule.updated_user = current_user.name
 		schedule.updated_count += 1
		db.session.commit()

	return jsonify(json=True)

@app.route('/schedule/', methods=['GET', 'POST'])
def schedule_list():
	date = [
		'2018-12', '2018-11', '2018-10', '2018-9', '2018-8', '2018-7', \
		'2018-6', '2018-5', '2018-4', '2018-3', '2018-2', '2018-1', \
		'2017-12', '2017-11', '2017-10', '2017-9', '2017-8', '2017-7', \
		'2017-6', '2017-5', '2017-4', '2017-3', '2017-2', '2017-1', \
		'2016-12', '2016-11', '2016-10', '2016-9', '2016-8', '2016-7', \
		'2016-6', '2016-5', '2016-4', '2016-3', '2016-2', '2016-1', \
		'2015-12', '2015-11', '2015-10', '2015-9', '2015-8', '2015-7', \
		'2015-6', '2015-5', '2015-4', '2015-3', '2015-2', '2015-1', \
		'2014-12', '2014-11', '2014-10', '2014-9', '2014-8', '2014-7', \
		'2014-6', '2014-5', '2014-4', '2014-3', '2014-2', '2014-1'
	]

	lists = []

	for i in date:		
		year, month = int(i.split('-')[0]), int(i.split('-')[1]) 
		schedules = Schedule.query.filter(Schedule.year==year, Schedule.month==month).all()

		if schedules:

			last_month_days = rrule(DAILY, dtstart=datetime.date(year, month-1, 26), \
				until=datetime.date(year, month, 1) - datetime.timedelta(days=1))
			this_month_days = rrule(DAILY, dtstart=datetime.date(year, month, 1), \
				until=datetime.date(year, month, 25))
	
			last_month = []
			this_month = []
		
			for day in last_month_days:
				last_month.append(1) if day.isoweekday() in [6, 7] else last_month.append(0)
			for day in this_month_days:
				this_month.append(1) if day.isoweekday() in [6, 7] else this_month.append(0)

			lists.append({
				'year': year, 
				'month': month, 
				'count': len(last_month)+len(this_month),
				'last_month': last_month, 
				'this_month': this_month, 
				'staffs': schedules
			})
			
	return render_template('schedule_list.html', lists=lists)

@app.route('/schedule/add/', methods=['GET', 'POST'])
@login_required
def schedule_add():
	users = User.query.order_by(User.id).all()
	return render_template('schedule_add.html', users=users)

@app.route('/schedule/edit/<int:year>/<int:month>/', methods=['GET', 'POST'])
@login_required
def schedule_edit(year, month):
	schedules = Schedule.query.filter(Schedule.year==year, Schedule.month==month).all()
	
	last_month_days = rrule(DAILY, dtstart=datetime.date(year, month-1, 26), \
			until=datetime.date(year, month, 1) - datetime.timedelta(days=1))
	this_month_days = rrule(DAILY, dtstart=datetime.date(year, month, 1), \
			until=datetime.date(year, month, 25))
	
	last_month = []
	this_month = []
		
	for day in last_month_days:
		last_month.append(1) if day.isoweekday() in [6, 7] else last_month.append(0)
	for day in this_month_days:
		this_month.append(1) if day.isoweekday() in [6, 7] else this_month.append(0)

	return render_template('schedule_edit.html', year=year, month=month, count=len(last_month)+len(this_month), \
		last_month=last_month, this_month=this_month, staffs=schedules)
