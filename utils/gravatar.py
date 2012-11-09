import urllib, hashlib
from django.core.urlresolvers import reverse

DEFAULT_GRAVATAR = "https://formhub.org/static/images/formhub_avatar.png"
GRAVATAR_ENDPOINT = "https://secure.gravatar.com/avatar/" 
GRAVATAR_SIZE = str(60)

def get_gravatar_img_link(user):
    url = GRAVATAR_ENDPOINT +\
        hashlib.md5(user.email.lower()).hexdigest() + "?" + urllib.urlencode({
            'd': DEFAULT_GRAVATAR, 's': str(GRAVATAR_SIZE)
        })
    return url

def gravatar_exists(user):
    url = GRAVATAR_ENDPOINT +\
        hashlib.md5(user.email.lower()).hexdigest() + "?" + "d=404"
    exists = urllib.urlopen(url).getcode() != 404
    return exists
