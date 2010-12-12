#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

from . import views

urlpatterns = patterns('',
    url(r"^/?$", views.dashboard),
    url(r"^(?P<name>.*)\.csv$", views.csv),
    url(r"^map/?", redirect_to, {'url': '/view'}),
    #4 main sections:
    url(r"^profiles/?$", views.profiles_section),
    url(r"^data/?$", views.submission_counts),
    url(r"^view/?$", views.view_section),
    url(r"^analysis/?$", views.analysis_section),
)
