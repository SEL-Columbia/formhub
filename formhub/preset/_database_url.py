# -*- coding: utf-8 -*-
""" given a URL of the form engine://user:password@server.domain:port/dbname?switches return database def

"""

# this modaule borrows freely from dj_database_url by Kenneth Reitz (to whom great thanks is due)

try:
    import urlparse  # Python 3 name
except ImportError:
    import urllib.parse as urlparse  # Python 2 equivalent

# Register database schemes in URLs.
urlparse.uses_netloc.append('postgres')
urlparse.uses_netloc.append('postgis')
urlparse.uses_netloc.append('mysql')
urlparse.uses_netloc.append('mysqlgis')
urlparse.uses_netloc.append('spatialite')
urlparse.uses_netloc.append('sqlite')

_DEFAULT_ENV = 'DATABASE_URL'

_SCHEMES = {
    'postgres': 'django.db.backends.postgresql_psycopg2',
    'postgis': 'django.contrib.gis.db.backends.postgis',
    'mysql': 'django.db.backends.mysql',
    'mysqlgis': 'django.contrib.gis.db.backends.mysql',
    'spatialite': 'django.contrib.gis.db.backends.spatialite',
    'sqlite': 'django.db.backends.sqlite3',
}


def config(url_string):
    """Returns configured DATABASE dictionary and query dictionary from url.
    @param url_string:
   --> {DATABASES_dictionary}, {dictionary of switches}
    """

    if url_string:
        url = urlparse.urlparse(url_string)

        # Remove leading '/'
        path = url.path[1:]

        # if we are using sqlite and we have no path, then assume we
        # want an in-memory database (this is the behaviour of sqlalchemy)
        if url.scheme == 'sqlite' and path == '':
            path = ':memory:'

        # Update with environment configuration.
        config = {
            'NAME': path,
            'USER': url.username or '',  # urlparse might return None for these attributes
            'PASSWORD': url.password or '',
            'HOST': url.hostname or '',
            'PORT': url.port or '',
            }

        try:
            config['ENGINE'] = _SCHEMES[url.scheme]
        except KeyError:
            raise ValueError('Unknown engine name "{}" for DATABASE_URL'.format(url.scheme))

        return config, urlparse.parse_qs(url.query)  # also make a dictionary of any queries (switches)

    else:  # url_string was blank
        return {}, {}
