# this system uses structured settings.py as defined in http://www.slideshare.net/jacobian/the-best-and-worst-of-django

from staging import *  # get most settings from staging.py (which in turn, imports from base.py)

# # # override the settings which came from staging # # # #
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
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql_psycopg2',
#        'NAME': 'formhub_dev',
#        'USER': 'formhub_dev',
#        'PASSWORD': '',
#        'HOST': 'localhost',
#        'OPTIONS': {
#            'autocommit': True,  # this option obsolete from django 1.6 & later
#        }
#    }
#}

# sqlite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

DATABASE_ROUTERS = []  # turn off second database for example

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'mlfs33^s1l4xf6a36$0#j%dd*sisfoi&)&4s-v=91#^l01v)*j'
