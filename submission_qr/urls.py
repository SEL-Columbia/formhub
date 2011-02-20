#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r"^$", views.list, name="list_quality_reviews"),
    url(r"^new/(?P<pi_id>\d+)/$", views.new_review),
    url(r"^(?P<show_hide>(show|hide))/(?P<qr_id>\d+)/$", views.show_hide),
    
#    url(r"^survey/(?P<pk>\d+)/$", views.survey),
)
