import urllib, hashlib
from django.core.urlresolvers import reverse

DEFAULT_GRAVATAR = "https://formhub.org/static/images/formhub_avatar.png"
GRAVATAR_ENDPOINT = "https://secure.gravatar.com/avatar/" 

def get_gravatar_img_link(user):
    email = user.email
    size = 40
    gravatar_url = GRAVATAR_ENDPOINT + hashlib.md5(email.lower()).hexdigest() +\
        "?" + urllib.urlencode({'d':DEFAULT_GRAVATAR, 's':str(size)})
    return [gravatar_url, gravatar_url == DEFAULT_GRAVATAR]
