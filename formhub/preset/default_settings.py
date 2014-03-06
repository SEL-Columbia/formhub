"""this preset uses a url-type string to implement 12-factor configuration with fewer environment variables.

DATABASE_URL = '<engine>://<user>:<password>@<host>:<port>/<database>'
       <engine> can be one of: 'postgresql', 'postgis', 'mysql', 'sqlite'
       (default: sqlite3 database file)
DJANGO_CONFIGURATION = 'Dev'  # use testing environment
DJANGO_SECRET_KEY = '<key of your invention>'
"""
import os
import warnings
import django.utils.six as six
import sys

# This module is compatible with ideas from:
#   dj_database_url by Kenneth Reitz
# and
#   django-configuration by Jannis Leidel
#
#
_url = os.getenv('DATABASE_URL', NotImplemented)

# try to guess whether we are testing based on environment variables
# be nice to users of django-configuration
_configuration = os.getenv('DJANGO_CONFIGURATION', NotImplemented)
if _configuration is NotImplemented:
    _testing = True if _url is NotImplemented else 'test' in _url
else:
    _testing = _configuration == 'Dev'

if _url is NotImplemented:
    DATABASES = NotImplemented
else:
    import dj_database_url
    DATABASES = {'default': dj_database_url.config(_url)}

if DATABASES is NotImplemented:  # no definition yet, use the local preset
    try:
        from local_preset import *   # is expected to import either staging or production itself
    except ImportError:
        six.reraise(RuntimeError, *sys.exc_info()[1:])  # use RuntimeError to extend the traceback
    except:
        raise
elif _testing:  # use our guess
    try:
        from staging import *  # get most settings from staging.py (which in turn, imports from ../settings.py)
    except ImportError:
        six.reraise(RuntimeError, *sys.exc_info()[1:])  # use RuntimeError to extend the traceback
    except:
        raise
else:
    try:
        from production import *  # which in turn imports from ../settings.py
    except ImportError:
        six.reraise(RuntimeError, *sys.exc_info()[1:])  # use RuntimeError to extend the traceback
    except:
        raise

# almost there.. allow local_settings to override anything that has happened.
try:    # permit those who wish to use local_settings the old way
    from ..local_settings import *
    warnings.warn('Legacy local_settings.py was imported.', ImportWarning)
except ImportError:
    pass
except:
    raise

# last of all, if nothing has defined a database, use sqlite
if DATABASES is NotImplemented:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
    print('Using default database {}'.format(os.path.abspath(DATABASES['default']['NAME'])))
