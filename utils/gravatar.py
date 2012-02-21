import urllib, hashlib
from django.core.urlresolvers import reverse

DEFAULT_GRAVATAR = "https://formhub.org/static/images/formhub_avatar.png"
GRAVATAR_ENDPOINT = "https://secure.gravatar.com/avatar/" 

def get_gravatar_img_link(user):
    email = user.email
    size = 40
    gravatar_base = GRAVATAR_ENDPOINT +\
        hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url = gravatar_base + "d=404"
    gravatar_exists = urllib.urlopen(gravatar_url).getcode() != 404
    gravatar_url = gravatar_base + urllib.urlencode({
        'd':DEFAULT_GRAVATAR, 's':str(size)
    })
    return [gravatar_url, gravatar_exists]
