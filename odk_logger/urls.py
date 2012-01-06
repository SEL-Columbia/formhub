#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import patterns, url
from odk_logger import views

urlpatterns = patterns('',
    url(r"^formList$", views.formList),
    url(r"^submission$", views.submission),
    url(r"^bulk-submission$", views.bulksubmission),
    url(r"^bulk-submission-form$", views.bulksubmission_form),
    url(r"^(?P<id_string>[^/]+)\.xml$", views.download_xform, name="download_xform"),
    url(r"^delete/(?P<id_string>[^/]+)/$", views.delete_xform),
    url(r"^(?P<id_string>[^/]+)/toggle_downloadable/$", views.toggle_downloadable),
)
