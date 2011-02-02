# EXAMPLE VALUES--
# Change these for your environment
# then copy then to "custom_settings.py"

import sys
from pymongo import Connection

MEDIA_URL = 'http://127.0.0.1:8000/site-media/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
}

# set up the Mongo Database, if we're testing clear the database out
_c = Connection()
MONGO_DB = None
if sys.argv[1]=="test":
    _c.drop_database("odk_test") # drop the database to clean it out
    MONGO_DB = _c.odk_test
else:
    MONGO_DB = _c.odk

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/Chicago'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SOUTH_IGNORE_DATABASES = ['mongodb']
