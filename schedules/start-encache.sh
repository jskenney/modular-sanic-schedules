#!/bin/bash

# Load the sched_* tables from MySQL into memcached (run from cron).
# Settings come from modular-sanic's .env (see sanic_env.py, or set ENV_FILE).
# Uses the virtual environment in VENV (default ../venv) when there is one,
# otherwise the python3 on the PATH (which needs pymysql, pymemcache, environs).

cd "$(dirname "$0")" || exit 1
VENV=${VENV:-../venv}
[ -f "$VENV/bin/activate" ] && source "$VENV/bin/activate"

python3 -B memcached-build.py
