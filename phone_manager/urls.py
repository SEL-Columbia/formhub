#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^$", views.phone_manager),
    url(r"^phones\.json$", views.phone_manager_json),
)

# from django.views.generic.simple import redirect_to
# urlpatterns = patterns('',
#     
#     
#     url(r"^couchly/(?P<survey_id>.*)$", views.couchly),
#     url(r"^embed/survey_instance_data/(?P<survey_id>.*)$", views.embed_survey_instance_data),
#     
#     url(r"^map/?", redirect_to, {'url': '/view'}),
#     url(r"^median-survey-times/?", views.survey_times),
#     url(r"^median-time-between-surveys/?", views.median_time_between_surveys),
#     #4 main sections:
# #    url(r"^data/activity$", views.recent_activity),
#     url(r"^view/?$", views.view_section),
#     url(r"^profiles/?$", views.profiles_section),
#     url(r"^analysis/?$", views.analysis_section),
#     url(r"^data/activity/(?P<stamp>\S*)$", data_sync.activity_list),
# )
