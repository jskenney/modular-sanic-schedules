###############################################################################
# Settings for the schedule scripts, read from modular-sanic's .env file
# (the same DB_* and MEMCACHED_* values the server uses).  The .env file is
# found by searching upward from this directory, or named with ENV_FILE:
#   ENV_FILE=/path/to/modular-sanic/.env python -B memcached-build.py
# Values already set in the environment win over the file.

import os
import environs

env = environs.Env()
env_path = env.read_env(os.environ.get('ENV_FILE'), recurse=not os.environ.get('ENV_FILE'), return_path=True)
if not env_path:
    print("Notice: no .env file found (set ENV_FILE), using the environment and defaults")

db_settings = {
    'DB_HOST': env.str('DB_HOST', default='127.0.0.1'),
    'DB_PORT': env.int('DB_PORT', default=3306),
    'DB_USER': env.str('DB_USER', default='username'),
    'DB_PASS': env.str('DB_PASS', default='password'),
    'DB_NAME': env.str('DB_NAME', default='dbname'),
}

memcached_settings = {
    'MEMCACHED_HOST': env.str('MEMCACHED_HOST', default='127.0.0.1'),
    'MEMCACHED_PORT': env.int('MEMCACHED_PORT', default=11211),
}
