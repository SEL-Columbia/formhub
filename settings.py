#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

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
    'json2xform',
    'odk_dropbox',
    'phone_manager',
)

MEDIA_URL   = 'http://localhost/site_media/'
MEDIA_ROOT  = os.path.join(PROJECT_ROOT, 'site_media/')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
    'mongodb': {
        'ENGINE': 'django_mongokit.mongodb',
        'NAME': 'odk',
    },
}


SOUTH_IGNORE_DATABASES = ['mongodb']

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# SEARCH ENGINE settings
HAYSTACK_SITECONF = 'search_sites'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = os.path.join(PROJECT_ROOT, 'search_index')
HAYSTACK_INCLUDE_SPELLING = True

try:
    import custom_settings
except ImportError:
    pass
