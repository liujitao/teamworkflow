# -*- coding: utf-8 -*-

import datetime, os, sys, json
import urllib, urllib2

from dateutil.relativedelta import relativedelta
from dateutil.rrule import *
    
from flask import render_template, redirect, url_for, request, jsonify, session, g
from flask_sqlalchemy import Pagination
from flask_login import login_user, logout_user, current_user, login_required

from sqlalchemy import desc

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase

from models import WorkLog, Wiki, User, Capture, Schedule, Task, GPN
from forms import WorkLogEditForm, UserEditForm, WikiEditForm, CaptureEditForm, LoginForm
from app import app, db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.errorhandler(401)
def page_unauthorized(error):
    return render_template('page_unauthorized.html'), 401

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@app.route('/')
def index():
    check_task_expire() # 检查过期的资源申请,提示回收
    assign_count = Task.query.filter(Task.status==1).count()
    execute_count = Task.query.filter(Task.status==2).count()
    aduit_count = Task.query.filter(Task.status==3).count()
    recycle_count = Task.query.filter(Task.type==1, Task.expire==1).count()

    return render_template('index.html', \
        assign_count=assign_count, execute_count=execute_count, \
        aduit_count=aduit_count, recycle_count=recycle_count)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    if form.validate_on_submit():
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.is_active and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))

    return render_template('login.html', form=form)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login')) 

@app.route('/link', methods=['GET'])
@login_required
def link():
    return render_template('link_change.html')

@app.route('/link_status/', methods=['GET'])
@login_required
def link_status():
    return render_template('link_status.html')

@app.route('/json/link', methods=['GET'])
@login_required
def get_link_info():
    links = { 
        '58.21.50.149': 'wx-1-ct',
        '122.9.252.135': 'wx-1-cu',
        '221.28.74.36': 'wx-2-ct',
        '58.24.27.100': 'wx-2-cu',
        '148.13.1.74': 'gpn',
        '69.19.34.29': 'dc',
        '173.5.34.11': 'la',
    } 

    hosts = ['69.19.34.27', '69.19.34.28', '173.5.34.12', '173.5.34.13']
    message = []
    for host in hosts:
        url = 'http://%s/rrd/link_info.json' % host
        response = urllib.urlopen(url)
        data = json.loads(response.read())
        response.close()

        name = data.keys()[0]
        traffic_in = data.values()[0]['in']
        traffic_out = data.values()[0]['out']
        connection = data.values()[0]['connection']
        current_link = links[data.values()[0]['current_link']]
        message.append((name, traffic_in, traffic_out, connection, current_link))

    return json.dumps(message)

@app.route('/json/link', methods=['POST'])
@login_required
def change_link():
    idc_name, link_name = request.args['idc'], request.args['link']
    playbook = '/tmp/link.yaml'

    links = { 
        u'wx-1-ct': '58.21.50.149',
        u'wx-1-cu': '122.9.252.135',
        u'wx-2-ct': '221.28.74.36',
        u'wx-2-cu': '58.24.27.100',
        u'gpn': '148.13.1.74',
        u'dc': '69.19.34.29',
        u'la': '173.5.34.11'
    } 

    generate_yaml(idc_name, links[link_name], playbook)
    task_result = ansible_task(playbook)
    #os.remove(playbook)
    
    return json.dumps(task_result)

@login_required
def generate_yaml(hosts, proxy_host, filename):
    import ruamel.yaml as yaml
    tmp = '''
- hosts: 
  gather_facts: no
  vars:
   - proxy_host: 
  become: yes
  become_method: sudo
  become_user: root

  tasks:
    - name: update /etc/hosts
      template: src=/opt/ansible/templates/hosts.j2 dest=/etc/hosts owner=root group=root mode=0644
      notify: 
        - restart dnsmasq
        - flush json

  handlers:
    - name: restart dnsmasq
      service: name=dnsmasq state=restarted
     
    - name: flush json
      shell: python link_info.py chdir=/opt/rrd
'''

    data = yaml.load(tmp, Loader=yaml.RoundTripLoader)
    data[0]['hosts'] = hosts
    data[0]['vars'][0]['proxy_host'] = proxy_host

    with open(filename, 'w') as f:
        yaml.dump(data, f, Dumper=yaml.RoundTripDumper, default_flow_style=False, indent=2)

@login_required
def ansible_task(playbooks):
    Options = namedtuple('Options', \
    ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'listhosts', 'listtasks', 'listtags', 'syntax'])

    options = Options(
        connection = 'ssh', 
        module_path = '/opt/ansible/modules',
        forks = 100, 
        become = True, 
        become_method = 'sudo', 
        become_user = 'root', 
        check = False, 
        listhosts = None,
        listtasks = None,
        listtags = None,
        syntax = None
    )

    loader = DataLoader()
    variable_manager = VariableManager()
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list='/opt/ansible/inventory')
    variable_manager.set_inventory(inventory)

    pb = PlaybookExecutor(playbooks=[playbooks], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=None)
    pb.run()

    stats = pb._tqm._stats
    ips = stats.processed.keys()
    return [ {ip : stats.summarize(ip)} for ip in ips ]

@app.route('/gpn/', methods=['GET'])
@login_required
def gpn():
    return render_template('gpn.html')

@login_required
def get_token():
    url = 'http://api.yun-idc.com/gic/v1/get_token/' 
    username = 'guest'
    password = 'guest'

    headers = {'username': username, 'password': password}
    req = urllib2.Request(url, headers=headers)
    resp = urllib2.urlopen(req).read()
    token = json.loads(resp)['Access-Token']

    return token

@app.route('/json/gpn/bandwidth', methods=['GET'])
@login_required
def get_gpn_bandwidth():
    token = get_token()

    url = 'http://api.yun-idc.com/gic/v1/app/info/?' + 'app_id=591c74ad-1ce0-477c-832a-926b1b2be45b'
    headers = {'token': token}
    
    req = urllib2.Request(url, headers=headers)
    resp = urllib2.urlopen(req).read()

    for i in json.loads(resp)['data'][0]['net']:
        if i['type'] == 'gic':
            id, qos = i['id'], i['qos']

    return jsonify({'name': 'gpn', 'id': id, 'qos': qos})

@app.route('/json/public/bandwidth', methods=['GET'])
@login_required
def get_public_bandwidth():
    list_vdc = [
        {'name': 'bj', 'app_id': '053f6f0b-a13b-4af3-80a5-395e205b0339'}, 
        {'name': 'wx', 'app_id': '173e23ad-7542-4ba4-929d-fecfc208d4b6'}, 
        {'name': 'la', 'app_id': '591c74ad-1ce0-477c-832a-926b1b2be45b'}
    ]

    list_public = []
    for vdc in list_vdc:
        url = 'http://api.yun-idc.com/gic/v1/app/info/?app_id=' + vdc['app_id']
        token = get_token()
        headers = {'token': token}
        
        req = urllib2.Request(url, headers=headers)
        resp = urllib2.urlopen(req).read()
    
        for i in json.loads(resp)['data'][0]['net']:
            if i['type'] == 'public':
                list_public.append({'name': vdc['name'], 'id': i['id'], 'qos': i['qos']})

    return json.dumps(list_public)

def increase_qos(old, new):
    qos = []
    
    while old < new:
        old += 100
        if old < new:
            qos.append(old)
        else:
            qos.append(new)

    return qos

def decrease_qos(old, new):
    qos = []

    while old > new:
        old -= 100
        if old > new:
            qos.append(old)
        else:
            qos.append(new)

    return qos

@app.route('/json/bandwidth', methods=['POST'])
@login_required
def set_bandwidth():
    bandwidth = { 
        'bj': {'id': 'f3c71d60-06b5-11e6-8224-0050569b1b91', 'qos': 50}, 
        'wx': {'id': 'c945c6f8-06d4-11e6-9366-0050569b1b91', 'qos': 50}, 
        'la': {'id': '024512a2-06b6-11e6-b951-0050569b1b91', 'qos': 100},
        'gpn': {'qos': 100}
    }
    
    name, action = request.json['name'], request.json['action']
    
    if action == 'on':
       qos = bandwidth[name]['qos']
    else:
       qos = 5

    if name == 'gpn':
        url = 'http://api.yun-idc.com/gic/v1/gpn/update/'
    else:
        url = 'http://api.yun-idc.com/gic/v1/public/update/' + bandwidth[name]['id']

    token = get_token()
    headers = {'token': token, 'Content-Type': 'application/json'}
    
    data = {'qos': qos, 'area_id': 'cn'}
    req = urllib2.Request(url, headers=headers, data=json.dumps(data))
    
    try:
    	resp = urllib2.urlopen(req).read()
        bandwidth = 'public %s set to: %d Mb' % (name, qos)
        status = json.loads(resp)['status']
        message = json.loads(resp)['messsage']
    except urllib2.HTTPError, e:
    	bandwidth = 'public %s set to: %d Mb' % (name, qos)
        status = json.loads(resp)['status']
        message = json.loads(resp)['errMsg']

    # change log
    gpn = GPN()
    gpn.bandwidth = bandwidth
    gpn.updated_user = current_user.name
    gpn.updated_time = datetime.datetime.now()
    gpn.status = status
    gpn.message = message
    
    db.session.add(gpn)
    db.session.commit()

    return json.dumps({'name': name, 'message': status + ':' + message})

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
        worklog.created_time = datetime.datetime.now()
        worklog.updated_time = datetime.datetime.now()
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
@login_required
def user_list():
    users = User.query.filter(User.active==1).order_by(User.id).all()
    return render_template('user_list.html', users=users)

@app.route('/user/add/', methods=['GET', 'POST'])
@login_required
def user_add():
    form = UserEditForm(request.form)
    form.team_id.choices = [(1, u'管理'), (2, u'运维监控'), (3, u'信号采集'), (4, u'网络存储'), \
        (5, u'机房运维'), (6, u'直播流运营')]
    form.team_id.choices.insert(0, (0, u'- 指定团队 -'))

    if form.validate_on_submit():
        user = User(form.name.data, form.email.data, form.qq.data, form.mobile.data, form.password.data, \
            form.team_id.data, form.active.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('user_list'))

    return render_template('user_edit.html', form=form)

@app.route('/user/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    user = User.query.filter(User.id==id).first()
    form = UserEditForm(request.form, user)
    form.team_id.choices = [(1, u'管理'), (2, u'运维监控'), (3, u'信号采集'), (4, u'网络存储'), \
        (5, u'机房运维'), (6, u'直播流运营')]
    form.team_id.choices.insert(0, (0, u'- 指定团队 -'))

    if form.validate_on_submit():
        form.populate_obj(user)

        if form.password.data != '':
            user.set_password(form.password.data)
        
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
@login_required
def wiki_list(page=1):
    record_per_page = app.config['RECORD_PER_PAGE']
    pagination = Wiki.query.order_by(Wiki.category_id, Wiki.id.desc()).paginate(page, record_per_page, False)
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
        wiki.created_time = datetime.datetime.now()
        wiki.updated_time = datetime.datetime.now()
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
@login_required
def wiki_detail(id):
    wiki = Wiki.query.filter(Wiki.id==id).first()
    return render_template('wiki_detail.html', wiki=wiki)

@app.route('/capture/', methods=['GET'])
@app.route('/capture/<int:page>/', methods=['GET', 'POST'])
@login_required
def capture_list(page=1):
    record_per_page = app.config['RECORD_PER_PAGE']
    pagination = Capture.query.order_by(Capture.location_id, Capture.hostname).paginate(page, record_per_page, False)
    captures = pagination.items
    return render_template('capture_list.html', pagination=pagination, record_per_page=record_per_page, \
        captures=captures)

@app.route('/capture/add/', methods=['GET', 'POST'])
@login_required
def capture_add():
    form = CaptureEditForm(request.form)
    form.location_id.choices = [(1, u'无锡新区'), (2, u'无锡国脉'), (3, u'北京中关村'), (4, u'北京铜牛'), (5, u'上海科技网'), (6, u'上海办公室'), (7, u'广州七星岗'), (8, u'长沙'), (9, u'安徽'), (10, u'山西'), (11, u'浙江'), (12, u'辽宁'), (13, u'四川'), (14, u'CIBN'), (15, u'上海教育网')]
    form.location_id.choices.insert(0, (0, u'- 指定位置 -'))
    form.model_id.choices = [(1, u'dell r410'), (2, u'dell r710'), (3, u'老双子星'), (4, u'超微双子星'), \
        (5, u'dell r420'), (6, u'dell r720'), (7, u'超微四子星')]
    form.model_id.choices.insert(0, (0, u'- 指定型号 -'))

    if form.validate_on_submit():
        capture = Capture()
        form.populate_obj(capture)
        capture.created_user = current_user.name
        capture.updated_user = current_user.name
        capture.created_time = datetime.datetime.now()
        capture.updated_time = datetime.datetime.now()
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
    form.location_id.choices = [ \
        (1, u'无锡新区'), (2, u'无锡国脉'), (3, u'北京中关村'), (4, u'北京铜牛'), (5, u'上海科技网'), \
        (6, u'上海办公室'), (7, u'广州七星岗'), (8, u'长沙'), (9, u'安徽'), (10, u'山西'), \
        (11, u'浙江'), (12, u'辽宁'), (13, u'四川'), (14, u'CIBN'), (15, u'上海教育网') \
    ]
    form.location_id.choices.insert(0, (0, u'- 指定位置 -'))
    form.model_id.choices = [(1, u'dell r410'), (2, u'dell r710'), (3, u'老双子星'), (4, u'超微双子星'), \
        (5, u'dell r420'), (6, u'dell r720'),  (7, u'超微四子星')]
    form.model_id.choices.insert(0, (0, u'- 指定型号 -'))

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
        days = [ datetime.date(year-1, 12, 25) + datetime.timedelta(days=i) for i in xrange(1, 5) ]
    else:
        days = [ datetime.date(year, month-1, 25) + datetime.timedelta(days=i) for i in xrange(1, 5) ]

    result  = [ {'name': str(day.month) + '-' + str(day.day) } for day in days ]
    return jsonify(json=result)

@app.route('/json/date/first_6days/', methods=['GET', 'POST'])
@login_required
def get_first_6days():
    '''
        获取前6天日期
    '''
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if month == 1:
        days = [ datetime.date(year-1, 12, 25) + datetime.timedelta(days=i) for i in xrange(1, 7) ]
    else:
        days = [ datetime.date(year, month-1, 25) + datetime.timedelta(days=i) for i in xrange(1, 7) ]

    result  = [ {'name': str(day.month) + '-' + str(day.day) } for day in days ]
    return jsonify(json=result)

@app.route('/json/schedule/init_commit/', methods=['GET', 'POST'])
@login_required
def schedule_init_commit():
    # print request.json['year'], request.json['month'], request.json['staff']
    year = int(request.json['year'])
    month = int(request.json['month'])

    if month == 1:
        start = datetime.date(year-1, 12, 26)
    else:
        start = datetime.date(year, month-1, 26)
    
    days = rrule(DAILY, dtstart=start, until=datetime.date(year, month, 25)).count()

    #staff [u'1,张三,12-26,1', u'2,李四,12-27,1', u'3,王五,12-28,1', u'4,候六,12-29,1',  u'5,孟七,12-26,2']

    # 排班处理
    separator = ','
    for staff in request.json['staff']:
        day = [0 for i in xrange(1, days+1)] # 数组初值0，代表全月休息

        id, name, start_date, type = staff.split(',')

        if int(type) == 1: # 1轮班，2白班 
            start_date_m, start_date_d = start_date.split('-')

            if month == 1:
                start_day_id = rrule(DAILY, dtstart=start, \
                    until=datetime.date(year-1, int(start_date_m), int(start_date_d))).count()
            else:
                start_day_id = rrule(DAILY, dtstart=start, \
                    until=datetime.date(year, int(start_date_m), int(start_date_d))).count()
        
            # 排班算法,4人2班,对4求余
            '''
            if start_day_id == 1:
                for i in xrange(1, days+1):
                    day[i-1] = (i % 4) if (i % 4) in [1, 2] else 0
            elif start_day_id == 2:
                for i in xrange(1, days+1):
                    day[i-1] = ((i - 1) % 4) if ((i - 1) % 4) in [1, 2] else 0
            elif start_day_id == 3:
                for i in xrange(2, days+1):
                    day[i-1] = ((i - 2) % 4) if ((i - 2) % 4) in [1, 2] else 0
            elif start_day_id == 4:
                day[0] = 2
                for i in xrange(3, days+1):
                    day[i-1] = ((i - 3) % 4) if ((i - 3) % 4) in [1, 2] else 0
            '''

            # 排班算法, 6人2班, 对6求余, 余2晚班, 余4晚班, 余1早班
            if start_day_id == 1:
                for i in xrange(1, days+1):
                    if (i % 6) == 1:
                        day[i-1] = 1
                    if (i % 6) in [2, 4]:
                        day[i-1] = 2
            elif start_day_id == 2:
                for i in xrange(1, days+1):
                    if ((i -1) % 6) == 1:
                        day[i-1] = 1    
                    if ((i -1) % 6) in [2, 4]:
                        day[i-1] = 2  
            elif start_day_id == 3:
                for i in xrange(2, days+1):
                    if ((i -2) % 6) == 1:
                        day[i-1] = 1    
                    if ((i -2) % 6) in [2, 4]:
                        day[i-1] = 2  
            elif start_day_id == 4:
                day[0]=2
                for i in xrange(3, days+1):
                    if ((i -3) % 6) == 1:
                        day[i-1] = 1    
                    if ((i -3) % 6) in [2, 4]:
                        day[i-1] = 2  
            elif start_day_id == 5:
                day[1] = 2
                for i in xrange(4, days+1):
                    if ((i -4) % 6) == 1:
                        day[i-1] = 1    
                    if ((i -4) % 6) in [2, 4]:
                        day[i-1] = 2  
            elif start_day_id == 6:
                day[0], day[2] = 2, 2
                for i in xrange(5, days+1):
                    if ((i -5) % 6) == 1:
                        day[i-1] = 1    
                    if ((i -5) % 6) in [2, 4]:
                        day[i-1] = 2  
        else:
            for i, v in enumerate(rrule(DAILY, dtstart=start, until=datetime.date(year, month, 25))):
                if v.weekday() in [0, 1, 2, 5, 6]:
                    day[i] = 1

        #保存数据库
        schedule = Schedule()
        schedule.name = name    
        schedule.year = year
        schedule.month = month
        schedule.days = days
        schedule.type = type
        schedule.list = separator.join([str(i) for i in day])
        schedule.morning =  0 if len([i for i in day if i == 1]) == 0 else len([i for i in day if i == 1])
        schedule.evening = len([i for i in day if i == 2])
        schedule.rest = 0
        schedule.overtime = 0
        
        schedule.updated_user = current_user.name
        schedule.updated_time = datetime.datetime.now()
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
        {'id': 1, 'type': 1, 'list': '1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0'},
        {'id': 2, 'type': 1, 'list': '1,2,0,0,1,2,0,0,1,2,0,0,1,2,0,0,25,2,0,0'},
        {'id': 3, 'type': 2, 'list': '1,0,0,0,0,25,0,3,0,0,0,0,0,0,0,13,0'},
        ...
    ]
    '''

    for staff in request.json['staff']:
        schedule = Schedule.query.filter(Schedule.year==request.json['year'], \
            Schedule.month==request.json['month'], Schedule.id==int(staff['id'])).first()

        schedule.list = staff['list']

        if staff['type'] == 1:
            schedule.morning = 0 if len([i for i in staff['list'].split(',') if i in ['1', '3']]) == 0 \
                else len([i for i in staff['list'].split(',') if i in ['1', '3']])
            schedule.evening = len([i for i in staff['list'].split(',') if i in ['2', '3']])

        if staff['type'] == 2:
            overtime = [int(i) for i in staff['list'].split(',') if i != '25']
            schedule.overtime = sum(overtime)

        schedule.rest = len([i for i in staff['list'].split(',') if i in ['25']])

        schedule.updated_user = current_user.name
        schedule.updated_time = datetime.datetime.now()
        schedule.updated_count += 1
        
        db.session.commit()
        
    return jsonify(json=True)

@app.route('/schedule/', methods=['GET'])
#@app.route('/schedule/<int:page>/', methods=['GET', 'POST'])
    #record_per_page = app.config['RECORD_PER_PAGE']
    #pagination = WorkLog.query.order_by(WorkLog.id.desc()).paginate(page, record_per_page, False)
    #worklogs = pagination.items
    #return render_template('worklog_list.html', pagination=pagination, record_per_page=record_per_page, \
    #   worklogs=worklogs)
def schedule_list(page=1):
    now = datetime.datetime.now()
    start_month = now + relativedelta(months=-10)
    end_month = now + relativedelta(months=3)
    date = [ str(i.year) + '-' + str(i.month) for i in list(rrule(MONTHLY, dtstart=start_month, until=end_month)) ]
    date.reverse()
    lists = []

    for i in date:
        year, month = int(i.split('-')[0]), int(i.split('-')[1])
        schedules = Schedule.query.filter(Schedule.year==year, Schedule.month==month).order_by(Schedule.type).all()
        
        if schedules:

            if month == 1:
                last_month_days = rrule(DAILY, dtstart=datetime.date(year-1, 12, 26), \
                    until=datetime.date(year, month, 1) - datetime.timedelta(days=1))
            else:
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
    #print lists            
    return render_template('schedule_list.html', lists=lists, current_year=now.year, current_month=now.month)

@app.route('/schedule/add/', methods=['GET', 'POST'])
@login_required
def schedule_add():
    years = []
    current = datetime.datetime.now()
    if current.month == 12:
        years.append(current.year)
        years.append(current.year+1)
    else:
        years.append(current.year)

    #users = User.query.filter(User.team_id==2, User.active==1).order_by(User.id).all()
    users = User.query.filter(User.active==1, User.id!=1, User.team_id==2).order_by(User.id).all()
    return render_template('schedule_add.html', users=users, years=years)

@app.route('/schedule/edit/<int:year>/<int:month>/', methods=['GET', 'POST'])
@login_required
def schedule_edit(year, month):
    schedules = Schedule.query.filter(Schedule.year==year, Schedule.month==month) \
        .order_by(Schedule.type).all()
    
    if month == 1:
        last_month_days = rrule(DAILY, dtstart=datetime.date(year-1, 12, 26), \
            until=datetime.date(year, month, 1) - datetime.timedelta(days=1))
    else:
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

@app.route('/schedule/delete/<int:year>/<int:month>/', methods=['GET', 'POST'])
@login_required
def schedule_delete(year, month):
    now = datetime.datetime.today()
    if month > now.month:
        db.session.query(Schedule).filter(Schedule.year==year, Schedule.month==month).delete()
        db.session.commit()
    return redirect(url_for('schedule_list'))

def check_task_expire():
    tasks = Task.query.filter(Task.type==1, Task.status==4).all()
    
    for task in tasks:
        if rrule(DAILY, dtstart=task.expired_time, until=datetime.datetime.now()).count() != 0:
            task.expire = 1
    
    db.session.commit()

@app.route('/task/', methods=['GET'])
@app.route('/task/status/<int:status>/', methods=['GET'])
@app.route('/task/page/<int:page>/', methods=['GET', 'POST'])
def task_list(page=1, status=None):
    record_per_page = app.config['RECORD_PER_PAGE']
    if not status:
        pagination = Task.query.order_by(Task.id.desc()).paginate(page, record_per_page, False)
    elif status==4:
        pagination = Task.query.filter(Task.type==1, Task.expire==1) \
            .order_by(Task.id.desc()).paginate(page, record_per_page, False)
    else:
        pagination = Task.query.filter(Task.status==status) \
            .order_by(Task.id.desc()).paginate(page, record_per_page, False)
    
    tasks = pagination.items

    ids = {}
    for t in Task.query.all():
        if t.executed_user_id:
            ids[t.id] = t.executed_user_id.split(',')

    return render_template('task_list.html', pagination=pagination, record_per_page=record_per_page, \
        tasks=tasks, ids=ids)

@app.route('/task/add', methods=['GET', 'POST'])
@app.route('/task/add/<int:id>/', methods=['GET', 'POST'])
def task_add(id=None):
    tasks = {}
    for task in Task.query.filter(Task.type==1, Task.status==4).order_by(Task.id.desc()).all():
        tasks[task.id] = {'title': task.title, 'expired_time': task.expired_time}

    return render_template('task_edit.html', id=id, tasks=tasks)

@app.route('/task/assign/<int:id>/', methods=['GET', 'POST'])
@login_required
def task_assign(id):
    task = Task.query.filter(Task.id==id).first()
    users = User.query.filter(User.active==1, User.id != 1).all()
    return render_template('task_assign.html', task=task, users=users)

@app.route('/task/execute/<int:id>', methods=['GET', 'POST'])
@login_required
def task_execute(id):
    task = Task.query.filter(Task.id==id).first()
    return render_template('task_execute.html', task=task)

@app.route('/task/audit/<int:id>',methods=['GET', 'POST'])
@login_required
def task_audit(id):
    task = Task.query.filter(Task.id==id).first()
    return render_template('task_audit.html', task=task)

@app.route('/task/detail/<int:id>',methods=['GET'])
def task_detail(id):
    task = Task.query.filter(Task.id==id).first()
    return render_template('task_detail.html', task=task)

@app.route('/json/task/create_commit/', methods=['GET', 'POST'])
def task_create_commit():
    #print request.json['title'], request.json['name'],request.json['team'], request.json['mobile']
    #print request.json['email'], request.json['expect_day'],request.json['type'], type(request.json['type'])
    #print request.json['hardware']

    task = Task()
    task.title = request.json['title']
    task.name = request.json['name']
    task.team = request.json['team']
    task.mobile = request.json['mobile']
    task.email = request.json['email']
    expect_day = int(request.json['expect_day'])
    task.planned_time =  datetime.datetime.now() + datetime.timedelta(days=expect_day)
    type = int(request.json['type'])
    task.type = type
    if type == 1:
        task.hardware = request.json['hardware']
        task.network = request.json['network']
        task.storage = request.json['storage']
        task.domain = request.json['domain']
        expire_month = int(request.json['expire_month'])
        task.expired_time =  datetime.datetime.now() + datetime.timedelta(days=expire_month*30)
    elif type == 2:
        task.recycle = request.json['recycle']
        task.link = request.json['link']
    elif type == 4:
        task.handle = request.json['handle']    

    task.created_user = request.json['name']
    task.created_time = datetime.datetime.now()
    task.status = 1

    db.session.add(task)
    db.session.commit()

    return jsonify(json=True)

@app.route('/json/task/assgin_commit/', methods=['GET', 'POST'])
@login_required
def task_assgin_commit():
    #print request.json['id'], request.json['execute']
    #print request.json['hardware']

    task = Task.query.filter(Task.id==request.json['id']).first()
    type = int(request.json['type'])

    if type == 1:
        task.hardware = request.json['hardware']
        task.network = request.json['network']
        task.storage = request.json['storage']
        task.domain = request.json['domain']
    elif type == 2:
        task.recycle = request.json['recycle']
    elif type == 4:
        task.handle = request.json['handle']

    task.executed_user_id = ','.join(request.json['execute'])

    ids = [int(id) for id in request.json['execute']]
    names = []
    for user in User.query.filter(User.active==1).all():
        if user.id in ids:
            names.append(user.name)

    task.executed_user = ','.join(names)
    task.assigned_user = current_user.name
    task.assigned_time = datetime.datetime.now()
    task.status = 2 

    db.session.commit()

    return jsonify(json=True)

@app.route('/json/task/execute_commit/', methods=['GET', 'POST'])
@login_required
def task_execute_commit():
    #print request.json['id'], request.json['type'], request.json['execute']
    task = Task.query.filter(Task.id==request.json['id']).first()
    task.execute = request.json['execute']
    type = int(request.json['type'])

    if type == 2:
        task.executed_commit_user = current_user.name
        task.executed_time = datetime.datetime.now()
        task.status = 3

    db.session.commit()

    return jsonify(json=True)

@app.route('/json/task/audit_commit/', methods=['GET', 'POST'])
@login_required
def task_audit_commit():
    #print request.json['id'], request.json['audit']
    task = Task.query.filter(Task.id==request.json['id']).first()
    task.audit = request.json['audit']
        
    task.audited_user = current_user.name
    task.audited_time = datetime.datetime.now()
    task.status = 4 

    if task.link != 0:
        apply = Task.query.filter(Task.id==task.link).first()
        apply.status = 5

    db.session.commit()
    
    return jsonify(json=True)
