#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import views
from . import forms
import submission_qr.forms as qr_forms

urlpatterns = patterns('',
    url(r"^$", views.list, name="list_quality_reviews"),
    url(r"^new/(?P<pi_id>\d+)/$", views.new_review),
    url(r"^(?P<show_hide>(show|hide))/(?P<qr_id>\d+)/$", views.show_hide),
    url(r"^post/(?P<instance_id>\d+)/(?P<reviewer_id>\d+)", qr_forms.ajax_post_form_create, name="post_qr_url"),
    url(r"^ajax_post/(?P<submission_id>\d+)/(?P<reviewer_id>\d+)", views.ajax_review_post),
    url(r"^list/(?P<submission_id>\d+)", views.list_reviews_for_submission),
    url(r"^score_partial/(?P<submission_id>\d+)/(?P<reviewer_id>\d+)", views.score_partial_request),
#    url(r"^survey/(?P<pk>\d+)/$", views.survey),
)
