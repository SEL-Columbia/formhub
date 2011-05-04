#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^survey-list/?$", views.export_list),
    url(r"^export_spreadsheet/(?P<id_string>[^/]*)\.csv$", views.csv_export),
    url(r"^export_spreadsheet/(?P<id_string>[^/]*)\.xls$", views.xls_export),
    url(r"^map_data_points/(?P<lga_id>\d+)/$", views.map_data_points),
    url(r"^survey/(?P<pk>\d+)/$", views.survey_responses),
    url(r"^survey_image_urls/(?P<pk>\d+)/$", views.survey_media_files),
    url(r"^access_denied/$", views.access_denied),

    # url(r"^median_survey_lengths/?$", views.median_survey_lengths),
    # url(r"^submission-counts/(\w+)/(\w+)$", views.frequency_table),
    # url(r"^surveyors/((?P<surveyor_id>\d+)/)?$", views.surveyors),
    # url(r"^surveys/((?P<survey_type_slug>\w+)/)?$", views.survey_types),
    # url(r"^counts-by-lga/?$", views.submission_counts_by_lga),
    
    url(r"^dashboard/$", views.dashboard, name="dashboard"),
    url(r"^$", views.dashboard, name="dashboard"),
)
