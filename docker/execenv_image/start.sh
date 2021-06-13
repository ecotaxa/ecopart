#! /usr/bin/env sh
set -e
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
mkdir /tmp/MPLCachemk
export MPLCONFIGDIR=/tmp/MPLCache
cd /app
#exec python3 run.py gunicorn
exec gunicorn --bind 0.0.0.0:8000 wsgilauncher:application
