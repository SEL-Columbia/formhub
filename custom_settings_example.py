# EXAMPLE VALUES--
# Change these for your environment
# then copy then to "custom_settings.py"

MEDIA_URL   = 'http://localhost/site_media/'
MEDIA_ROOT  = '/path/to/project/site_media/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tmp/db.sqlite3',
    }
}

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/Chicago'

DEBUG = True
TEMPLATE_DEBUG = DEBUG
