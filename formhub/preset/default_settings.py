# this system uses structured settings.py as defined in http://www.slideshare.net/jacobian/the-best-and-worst-of-django
#
# this third-level staging file overrides some definitions in staging.py
# You may wish to alter it to agree with your local environment
#

from staging_example import *  # get most settings from staging_example.py (which in turn, imports from settings.py)

# # # now override the settings which came from staging # # # #

# choose a different database...
# sqlite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

DATABASE_ROUTERS = []  # turn off second database

# Make a unique unique key just for testing, and don't share it with anybody.
SECRET_KEY = 'mlfs33^s1l4xf6a36$0#j%dd*sisfoi&)&4s-v=91#^l01v)*j'
