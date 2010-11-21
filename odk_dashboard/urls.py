#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^/?$", views.dashboard),
    url(r"^submission-counts$", views.submission_counts),
    url(r"^(?P<survey_type>.*)\.csv$", views.csv),
)
