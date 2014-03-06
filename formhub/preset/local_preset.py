# this top-level staging file overrides some definitions in staging.py

# Alter this skeleton to agree with the needs of your local environment

# Use it by setting your DJANGO_SETTINGS_MODULE environment variable to this module,
# using something like: export DJANGO_SETTINGS_MODULE="myproject.preset.local_preset"
# or select it from the command line like:  python manage.py somecommand --settings=myproject.preset.local_preset

# Note: if you are using a 12-Factor configuration scheme, you very likely should not be using this file

from staging import *  # get most settings from staging.py (which in turn, imports from settings.py)

# # # now you can override the settings which came from staging # # # #

# for axample, choose a different database...
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': 'db.sqlite',
#    }
#}
