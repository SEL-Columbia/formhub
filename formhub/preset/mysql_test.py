# this system uses structured settings.py as defined in http://www.slideshare.net/jacobian/the-best-and-worst-of-django
#
# this example third-level staging file overrides some definitions in staging_example.py
# so that it returns the same definitions as the former localsettings.py.examples in the formhub distribution.
#

from staging_example import *  # get most settings from staging_example.py (which in turn, imports from settings.py)

# # # now override the settings which came from staging # # # #

# choose a different database...
# mysql
DATABASES = {
    'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'test',
    'USER': 'adotest',
    'PASSWORD': '12345678',  # in production, use something like: os.environ['MY_DB_PASSWORD']
    'HOST': '25.116.170.194'
    }
}

# Make a unique unique key just for testing, and don't share it with anybody.
SECRET_KEY = 'mlfs33^s1l4xf6a36$0#j%dd*sisfoi&)&4s-v=91#^l01v)*j'
