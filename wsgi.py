#!/usr/bin/env python

activate_this = '/opt/project/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/opt/project/teamworkflow')

from app import app

if __name__ == '__main__':
    app.run()
