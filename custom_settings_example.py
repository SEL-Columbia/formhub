# EXAMPLE VALUES--
# Change these for your environment
# then copy then to "custom_settings.py"

MEDIA_URL   = 'http://localhost/site_media/'

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

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/Chicago'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SOUTH_IGNORE_DATABASES = ['mongodb']
