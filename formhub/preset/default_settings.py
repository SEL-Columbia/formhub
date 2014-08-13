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

# These are necessary for running on Amazon Web Services (AWS)
# because basic formhub/django functions which rely on email,
# such as new account registration, will fail

AWS_ACCESS_KEY_ID =     '' # find these in your AWS console
AWS_SECRET_ACCESS_KEY = ''
EMAIL_BACKEND = 'django_ses.SESBackend'
DEFAULT_FROM_EMAIL = '' # e.g., 'no-reply@example.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Uncomment the following three lines if you are using
# an AWS S3 Bucket as the default file store, and define
# your bucket name in the AWS_STORAGE_BUCKET_NAME variable.
# This is optional, but strong recommended.

#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
#AWS_STORAGE_BUCKET_NAME = '' # use your S3 Bucket name here
#AWS_DEFAULT_ACL = 'private'

# In this example we are supplementing the django database
# definition found in the ../settings.py file with a password
# (normally we wouldn't check this into source control, but this
# is here just for illustration, as an example of what's possible)

DATABASES['default']['PASSWORD'] = 'foo'
# an alternative to hard-coding the password string
# is to define the db password as an environment variable:
#DATABASES['default']['password'] = os.environ['FORMHUB_DB_PWD']

# Examples of other over-rides you could do here:

DATABASE_ROUTERS = [] # turn off second database

# Make a unique unique key just for testing, and don't share it with anybody.
SECRET_KEY = 'mlfss33^s1l4xf6a36$0#j%dd*sisfoi&)&4s-v=91#^l01v)*j'

