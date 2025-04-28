#!/bin/bash

source ../venv/bin/activate

cat memcached-build.py | grep -v 'mcache.set' > memcached-purge.py
python -B memcached-purge.py
rm -f memcached-purge.py
