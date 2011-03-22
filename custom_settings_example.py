# We have broken the standard settings.py into two files:
# 1. settings.py: this contains settings that will not change across
#    different deployments of this code.
# 2. custom_settings.py: this contains settings that are likely to
#    change across deployments.
# If you are setting up this project for the first time, copy
# custom_settings_example.py to custom_settings.py and modify these
# custom settings as you needed for your environment.

MEDIA_URL = 'http://127.0.0.1:8000/site-media/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
}

MONGO = {
    "database name" : "odk",
    "test database name" : "odk_test",
    }

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

