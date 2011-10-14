#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from odk_viewer import views

urlpatterns = patterns('',
    url(r"^export_spreadsheet/(?P<id_string>[^/]*)\.csv$", views.csv_export),
    url(r"^export_spreadsheet/(?P<id_string>[^/]*)\.xls$", views.xls_export),
    url(r"^survey/(?P<pk>\d+)/$", views.survey_responses),
    url(r"^map/(?P<id_string>[^/]*)/$", views.map),
)
