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

from formhub.settings import *

# For this example configuration, we are running the server in
# debug mode, but this should be changed to False for a server
# in production (changing the value of DEBUG also requires that
# ALLOWED_HOSTS, below, be defined as well)

DEBUG = True

# Hosts/domain names that aare valid for this site
# This is required if DEBUG is False, otherwise the serever
# will respond with 500 errors:
# https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
#ALLOWED_HOSTS = ['.example.com']

# In this example we are supplementing the django database
# definition found in the ../settings.py file with a password
# (normally we wouldn't check this into source control, but this
# is here just for illustration, as an example of what's possible)

#DATABASES['default']['PASSWORD'] = 'foo'
# an alternative to hard-coding the password string
# is to define the db password as an environment variable:
#DATABASES['default']['password'] = os.environ['FORMHUB_DB_PWD']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

# Examples of other over-rides you could do here:

DATABASE_ROUTERS = [] # turn off second database

# Make a unique unique key just for testing, and don't share it with anybody.
SECRET_KEY = 'mlfss33^s1l4xf6a36$0#j%dd*sisfoi&)&4s-v=91#^l01v)*j'

