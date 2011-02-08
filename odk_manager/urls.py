#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^formList$", views.formList),
    url(r"^submission$", views.submission),

    url(r"^create-xform/$", views.create_xform),
    url(r"^list-xforms/$", views.list_xforms, name="list-xforms"),
    url(r"^update-xform/(?P<pk>\d+)/$", views.update_xform),
)
