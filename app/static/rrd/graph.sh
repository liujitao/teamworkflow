#!/bin/bash

cd /opt/project/teamworkflow/app/static/rrd

[ ! -d us-1-219 ] && mkdir us-1-219
[ ! -d us-1-220 ] && mkdir us-1-220
[ ! -d la-1-219 ] && mkdir la-1-219
[ ! -d la-1-220 ] && mkdir la-1-220

curl http://69.19.34.27/rrd/download.png -o us-1-219/download.png
curl http://69.19.34.27/rrd/loss.png -o us-1-219/loss.png
curl http://69.19.34.27/rrd/ping.png -o us-1-219/ping.png

curl http://69.19.34.28/rrd/download.png -o us-1-220/download.png
curl http://69.19.34.28/rrd/loss.png -o us-1-220/loss.png
curl http://69.19.34.28/rrd/ping.png -o us-1-220/ping.png

curl http://173.5.34.13/rrd/download.png -o la-1-219/download.png
curl http://173.5.34.13/rrd/loss.png -o la-1-219/loss.png
curl http://173.5.34.13/rrd/ping.png -o la-1-219/ping.png

curl http://173.5.34.12/rrd/download.png -o la-1-220/download.png
curl http://173.5.34.12/rrd/loss.png -o la-1-220/loss.png
curl http://173.5.34.12/rrd/ping.png -o la-1-220/ping.png
