import os
from custom_settings import *

MANAGERS = ADMINS

LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

ADMIN_MEDIA_PREFIX = '/media/'

# settings for user authentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

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
    'djangomako.middleware.MakoMiddleware',
)

ROOT_URLCONF = 'nmis.urls'

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT  = '%s/site_media/' % PROJECT_ROOT

TEMPLATE_DIRS = (
    "%s/base_templates/" % PROJECT_ROOT
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'south',
    'eav',

    'odk_dashboard',
    'odk_dropbox',
)
