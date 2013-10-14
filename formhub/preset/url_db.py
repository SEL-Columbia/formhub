"""this preset uses a url-type string to implement 12-factor configuration with fewer environment variables.

DATABASE_URL = '<engine>://<user>:<password>@<host>:<port>/<database>'
       <engine> can be one of: 'postgresql', 'postgis', 'mysql', 'sqlite'
       (default: sqlite3 database file)
DJANGO_CONFIGURATION = 'Dev'  # use testing environment
DJANGO_SECRET_KEY = '<key of your invention>'
"""
import os

configuration = os.getenv('DJANGO_CONFIGURATION', 'Dev')
if configuration == 'Dev':
    from staging_example import *  # get most settings from staging_example.py (which in turn, imports from settings.py)
else:
    from production_example import *

url = os.getenv('DATABASE_URL')

if url:
    import dj_database_url
    DATABASES = {'default': dj_database_url.config(url)}

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    }

# Make a unique unique key (with a default for testing), and don't share it with anybody.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'xmlfs33xPBHTCR6a36$0#j%dd*sis')
