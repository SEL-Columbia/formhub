"""local_preset.py is imported by default_settings.py when no URL environment variable is defined.
"""
#
# Alter this skeleton to agree with the needs of your local environment

# Note: if you are using a URL 12-Factor configuration scheme, you will not be using this file

# important thing we do here is to import all those symbols that are defined in settings.py
from ..settings import *  # get most settings from ../settings.py

# or perhaps you would prefer something like:
# from staging import *  # which in turn imports ../settings.py 


# # # and now you can override the settings which we just got from settings.py # # # #

# for example, choose a different database...
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': 'db.sqlite',
#    }
#}
# or:
#DEBUG = True

