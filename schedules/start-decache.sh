#!/bin/bash

# Remove the schedule keys that memcached-build.py would write (it runs the
# build script without its mcache.set lines, so only the deletes remain).
# Settings and VENV as in start-encache.sh.

cd "$(dirname "$0")" || exit 1
VENV=${VENV:-../venv}
[ -f "$VENV/bin/activate" ] && source "$VENV/bin/activate"

grep -v 'mcache.set' memcached-build.py > memcached-purge.py
python3 -B memcached-purge.py
rm -f memcached-purge.py
