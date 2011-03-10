#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from custom_settings import *

import sys
from pymongo import Connection

# set up the Mongo Database
_c = Connection()
MONGO_DB = None
if sys.argv[1]=="test":
    # if we're testing, clear the database out
    # note: this only works when we run the tests at the command line
    _c.drop_database(MONGO["test database name"])
    MONGO_DB = _c[MONGO["test database name"]]
else:
    MONGO_DB = _c[MONGO["database name"]]

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

ADMIN_MEDIA_PREFIX = '/media/'

# settings for user authentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# user registration settings
ACCOUNT_ACTIVATION_DAYS = 1

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'f6h^bz8&0+ad@+qsntr)_onhx2(y^^u%$434byw3l^q!*n078v'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'nmis.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "base_templates/" )
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'south',
    'registration',

    'pyxform',
    'locations',
    'parsed_xforms',
    'phone_manager',
    'surveyor_manager',
    'xform_manager',
    'map_xforms',
    'submission_qr',
)

# SEARCH ENGINE settings
HAYSTACK_SITECONF = 'search_sites'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = os.path.join(PROJECT_ROOT, 'search_index')
HAYSTACK_INCLUDE_SPELLING = True
