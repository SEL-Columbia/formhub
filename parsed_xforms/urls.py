#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^export_spreadsheet/(?P<id_string>[^/]*)\.csv$", views.csv_export),
    url(r"^export_spreadsheet/(?P<id_string>[^/]*)\.xls$", views.xls_export),
    url(r"^survey/(?P<pk>\d+)/$", views.survey_responses),
    url(r"^survey_image_urls/(?P<pk>\d+)/$", views.survey_media_files),
    url(r"^access_denied/$", views.access_denied),

    url(r"^dashboard/$", views.dashboard, name="dashboard"),
    url(r"^$", views.dashboard, name="dashboard"),
)
