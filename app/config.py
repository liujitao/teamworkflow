# -*- coding: utf-8 -*-

import os
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = 'static/upload'
UPLOAD_MAX_SIZE = 1024 * 1024 * 200 # 200M
UPLOAD_ALLOWED_EXTENSIONS = set(['conf', 'ini', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', \
							'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'sql', 'csv', \
							'tar.gz', 'zip', 'rar'])

#SQLALCHEMY_DATABASE_URI = 'mysql://team:team@localhost/team'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(APP_ROOT, 'team.db')
SQLALCHEMY_ECHO = 'True'

CSRF_ENABLED = True
SECRET_KEY = 'tvm'

RECORD_PER_PAGE = 20
