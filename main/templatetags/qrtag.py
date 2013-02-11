from django.utils.safestring import mark_safe
from django import template
register = template.Library()

from utils.viewer_tools import enketo_url
from utils.qrcode import generate_qrcode

@register.simple_tag
def qrcode(username, idstring):
    url = enketo_url(username, idstring)
    image = generate_qrcode(url) 
    img = mark_safe(u"""<img class="qrcode" src="%s" width="150" height="150" alt="%s" />""" % (image, url))
    return image
