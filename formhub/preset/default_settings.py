# This system uses structured settings.py as defined in the 
# second from last slide in this presentation:
# http://www.slideshare.net/jacobian/the-best-and-worst-of-django

# The basic idea is that a file like this, which is referenced when
# the django app runs, imports from ../settings.py, and over-rides
# and value there with a value specified here

# This file is checked into source control as an example, but 
# your actual production settings, which contain database passwords
# and 3rd party private keys, etc., should perhaps be omitted using
# .gitignore

from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'FormhubDjangoDB',
        'USER': 'formhubDjangoApp',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',                      # Set to empty string for default.
    }
}

