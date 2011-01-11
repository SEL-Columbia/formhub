#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    # list that ODK Collect uses to download forms
    url(r"^formList$", views.formList),
    # url where ODK Collect submits data
    url(r"^submission$", views.submission),
    url(r"^survey-list/?$", views.survey_list),
    url(r"^(?P<title>[^/]*)\.xls$", views.xls),
    url(r"^content/(?P<topic>\w*)/?$", views.content),
)
