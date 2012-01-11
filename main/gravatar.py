import urllib, hashlib
from django.core.urlresolvers import reverse

def get_gravatar_img_link(user):
    email = user.email
    default = "http://www.formhub.org/static/images/formhub_avatar.png"
    size = 40
    gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
    return gravatar_url
