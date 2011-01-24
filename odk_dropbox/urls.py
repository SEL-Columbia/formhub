#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    # list that ODK Collect uses to download forms
    url(r"^formList$", views.formList),
    # url where ODK Collect submits data
    url(r"^submission$", views.submission),
    url(r"^survey-list/?$", views.export_list),
    url(r"^(?P<title>[^/]*)\.xls$", views.xls),
    url(r"^odk/", views.dashboard),
    url(r"^data/map_data/?$", views.map_data_points),
)

# from django.views.generic.simple import redirect_to
# urlpatterns = patterns('',
#     url(r"^/?$", views.ensure_logged_in),
#     url(r"^main/?$", views.main_index),
#     url(r"^couchly/(?P<survey_id>.*)$", views.couchly),
#     url(r"^embed/survey_instance_data/(?P<survey_id>.*)$", views.embed_survey_instance_data),
#     url(r"^rapid_odk/$", views.dashboard),
#     url(r"^map/?", redirect_to, {'url': '/view'}),
#     url(r"^median-survey-times/?", views.survey_times),
#     url(r"^median-time-between-surveys/?", views.median_time_between_surveys),
#     url(r"^submission-counts/?$", views.frequency_table_urls),
#     url(r"^submission-counts/(\w+)/(\w+)$", views.frequency_table),
#     #4 main sections:
# #    url(r"^data/activity$", views.recent_activity),
#     url(r"^view/?$", views.view_section),
#     url(r"^profiles/?$", views.profiles_section),
#     url(r"^analysis/?$", views.analysis_section),
#     url(r"^data/activity/(?P<stamp>\S*)$", data_sync.activity_list),
# )
