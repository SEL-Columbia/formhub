# this system uses structured settings.py as defined in http://www.slideshare.net/jacobian/the-best-and-worst-of-django

from base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
TEMPLATE_STRING_IF_INVALID = '***Invalid Template String***'

# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

# mysql
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'formhub_dev',
#        'USER': 'formhub_dev',
#        'PASSWORD': '',
#    }
#}

#postgres
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'formhub_dev',
        'USER': 'formhub_dev',
        'PASSWORD': '',
    },
    'gis': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'phis',
        'USER': 'nomadstaff',
        'PASSWORD': 'nopolio',
        'HOST': 'localhost',
        'OPTIONS': {
            'autocommit': True,
        }
    }
}

TIME_ZONE = 'UTC'

TOUCHFORMS_URL = 'http://localhost:9000/'

MONGO_DATABASE = {
    'HOST': 'localhost',
    'PORT': 27017,
    'NAME': 'formhub',
    'USER': '',
    'PASSWORD': ''
}
SECRET_KEY = 'mlfs33^s1l4xf6a36$0#srgcpj%dd*sisfo6HOktYXB9y'

# Clear out the test database
if TESTING_MODE:
    MONGO_DB.instances.drop()
