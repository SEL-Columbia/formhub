# We have broken the standard settings.py into two files:
# 1. settings.py: this contains settings that will not change across
#    different deployments of this code.
# 2. custom_settings.py: this contains settings that are likely to
#    change across deployments.
# If you are setting up this project for the first time, copy
# custom_settings_example.py to custom_settings.py and modify these
# custom settings as you needed for your environment.

# Is this really going to help us over having a single settings.py
# example? I think Alex has the answer to this question. -Andrew

import os, re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

MEDIA_URL = 'http://127.0.0.1:8000/site-media/'
MEDIA_ROOT  = os.path.join(PROJECT_ROOT, 'site_media/')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
}

try:
    if sys.argv[1]=="test":
        TESTING=True
    else:
        TESTING = False
except:
    TESTING = False

REPOSITORY_ENVIRONMENT = "dev"

#this is a bad way to do this, but it works for our needs...
# /path/to/repos/production/... will use production
#   "  staging/... will use staging
# all else will be dev.
__repo_env = "dev"
if re.search(PROJECT_ROOT, "production"):
    __repo_env = "production"
elif re.search(PROJECT_ROOT, "staging"):
    __repo_env = "staging"

REPOSITORY_ENVIRONMENT = __repo_env

MONGO = {
    "database name" : "%s_odk" % REPOSITORY_ENVIRONMENT,
    "test database name" : "%s_odk_test" % REPOSITORY_ENVIRONMENT,
    }


ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

STRICT = False
