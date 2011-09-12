#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from . import views

# Here are some url names that we'll need to reference multiple times.
DOWNLOAD_XFORM = "download_xform"
LIST_XFORMS = "list_xforms"
FORM_LIST = "form_list"

USERNAME = "((?P<username>[^/]+)/)?"

urlpatterns = patterns('',
    url(r"^%sformList$" % USERNAME, views.formList, name=FORM_LIST),
    url(r"^%ssubmission$" % USERNAME, views.submission),

    url(r"^%sxform/new/$" % USERNAME, views.create_xform),
    url(r"^%sxform/(?P<id_string>[^/]+)\.xml$" % USERNAME, views.download_xform, name=DOWNLOAD_XFORM),
    url(r"^xform/toggle_downloadable/(?P<id_string>[^/]+)/$", views.toggle_downloadable),
    url(r"^submission_test_form/?$", views.submission_test_form),
    url(r"^xform/(?P<id_string>[^/]+)/$", views.update_xform),
    url(r"^%s$" % USERNAME, views.list_xforms, name=LIST_XFORMS),
    url(r"^survey/(?P<pk>\d+)/$", views.instance),
)
