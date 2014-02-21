# this system uses structured settings.py as defined in http://www.slideshare.net/jacobian/the-best-and-worst-of-django

from formhub.settings import *

DEBUG = False  # this setting file will not work on "runserver" -- it needs a server for static files
TESTING_MODE = False  # used by celery startup


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# override to set the actual location for the production static and media directories
MEDIA_ROOT = '/var/formhub-media'
STATIC_ROOT = "/srv/formhub-static"
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "static"),
)

# your actual production settings go here...,.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'formhub',
        'USER': 'formhub_prod',
        'PASSWORD': os.environ['FORMHUB_PROD_PW'],  # the password must be stored in an environment variable
        'HOST': os.environ.get("FORMHUB_DB_SERVER", 'dbserver.yourdomain.org'), # the server name may be in env
        'OPTIONS': {
            'autocommit': True,   # note: this option obsolete starting with django 1.6
        }
    },
    'gis': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'phis',
        'USER': 'staff',
        'PASSWORD': os.environ['PHIS_PW'],  # the password must be stored in an environment variable
        'HOST': 'gisserver.yourdomain.org',
        'OPTIONS': {
            'autocommit': True,
        }
    }
}

#
ALLOWED_HOSTS = ['my.domain.name.com']

DATABASE_ROUTERS = ['formhub.preset.dbrouter.GisRouter']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'America/New_York'
TIME_ZONE = 'Africa/Lagos'

EMAIL_HOST =  'smtp.gmail.com'
#Default: 'localhost'
#The host to use for sending email.
#
#See also EMAIL_PORT.
EMAIL_HOST_PASSWORD = '<thisisnotreallymypassword>'
#Password to use for the SMTP server defined in EMAIL_HOST. This setting is used in conjunction with EMAIL_HOST_USER when authenticating to the SMTP server. If either of these settings is empty, Django won’t attempt authentication.
#
EMAIL_HOST_USER = 'do.not.reply@mydomain.com'
#Default: '' (Empty string)
#Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won’t attempt authentication.
#
#EMAIL_PORT
#Default: 25
#Port to use for the SMTP server defined in EMAIL_HOST.
#
#EMAIL_SUBJECT_PREFIX
#
#Default: '[Django] '
#
#Subject-line prefix for email messages sent with django.core.mail.mail_admins or django.core.mail.mail_managers. You’ll probably want to include the trailing space.
#EMAIL_USE_TLS
#Default: False
#Whether to use a TLS (secure) connection when talking to the SMTP server. This is used for explicit TLS connections, generally on port 587. If you are experiencing hanging connections, see the implicit TLS setting EMAIL_USE_SSL.

# If you want to use web forms, you must either build an Enketo server, or sign up for an account at enketo.org
ENKETO_URL = 'https://enketo.org/'
ENKETO_API_TOKEN = '<the API token they assign goes here>'

TOUCHFORMS_URL = 'http://localhost:9000/'

MONGO_DATABASE = {
    'HOST': 'localhost',
    'PORT': 27017,
    'NAME': 'formhub',
    'USER': '',
    'PASSWORD': ''
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'mlfs33^s1l4xf6a36$0#j%dd*sisfo6HOktYXB9y'
