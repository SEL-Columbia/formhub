# To use, run an smtpd.DebuggingServer in a separate shell
#   $ sudo python -m smtpd -c DebuggingServer -n localhost:25
#
# Then test by running a shell with this as the settings file
#   $ python manage.py shell --settings=formhub.preset.smtp_debugging
#   > import logging
#   > logger = logging.getLogger('django.request')
#   > logger.log('A celery error occurred')
#
# You should see an email message on the smtpd.DebuggingServer's shell
#
from formhub.settings import *

DEBUG = False

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
ADMINS = (
    ('Admin', 'admin@example.com'),
)