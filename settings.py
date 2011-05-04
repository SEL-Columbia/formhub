#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

#This is for xform_manager.
#we should probably make this var name more specific
STRICT = True

from custom_settings import *

import sys
from pymongo import Connection

# set up the Mongo Database
_c = Connection()
MONGO_DB = None
TESTING_MODE = False

if len(sys.argv)>=2 and (sys.argv[1]=="test" or sys.argv[1]=="test_all"):
    # This trick works only when we run tests from the command line.
    TESTING_MODE = True
    MONGO_DB = _c[MONGO["test database name"]]
else:
    TESTING_MODE = False
    MONGO_DB = _c[MONGO["database name"]]

# Clear out the test database
if TESTING_MODE:
    MONGO_DB.instances.drop()
    MEDIA_ROOT  = os.path.join(PROJECT_ROOT, 'test_site_media/')
else:
    MEDIA_ROOT  = os.path.join(PROJECT_ROOT, 'site_media/')
    

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

ADMIN_MEDIA_PREFIX = '/media/'

# settings for user authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'

# user registration settings
ACCOUNT_ACTIVATION_DAYS = 1

# Make the SECRET_KEY unique, and don't share it with anybody.  --d'oh!

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

TEMPLATE_DEBUG=True
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

    'locations',
    'parsed_xforms',
    'nga_districts',
    'phone_manager',
    'surveyor_manager',
    'xform_manager',
    'map_xforms',
    'submission_qr',
    
    #required for django-sentry
    'indexer',
    'paging',
    'sentry',
    'sentry.client',
)

# SEARCH ENGINE settings
HAYSTACK_SITECONF = 'search_sites'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = os.path.join(PROJECT_ROOT, 'search_index')
HAYSTACK_INCLUDE_SPELLING = True
