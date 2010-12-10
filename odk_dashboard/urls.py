#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^/?$", views.dashboard),
    url(r"^data$", views.submission_counts),
    url(r"^(?P<name>.*)\.csv$", views.csv),
    url(r"^map/?$", views.map_submissions),
    #4 main sections:
    url(r"^profiles/?$", views.profiles_section),
    url(r"^data/?$", views.data_section),
    url(r"^view/?$", views.view_section),
    url(r"^analysis/?$", views.analysis_section),
)
