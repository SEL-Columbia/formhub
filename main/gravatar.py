import urllib, hashlib


def get_gravatar_img_link(user):
    email = user.email
    default = "http://www.example.com/default.jpg"
    size = 40
    gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
    #print "gravatar url for %s: %s" % (email, gravatar_url)
    return gravatar_url
