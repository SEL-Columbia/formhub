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

#ODK Collect URLS:
#-general:
#    /formList
#    /submission
#-group-specific:
#    /group_name/formList
#    /group_name/submission

#browser accessible urls
#-general:
#    /
#    /xform/new
#    /xform/show
#    /xform/hide
#    /xform/(xform_id) #edit
#    /xform/(xform_id).xml #download
#-group-specific:
#    /group_name/
#    /group_name/xform/new
#    /group_name/xform/show
#    /group_name/xform/hide
#    /group_name/xform/(xform_id)
#    /group_name/xform/(xform_id).xml

#For debugging with no groups: OPT_GROUP_REGEX = ""
OPT_GROUP_REGEX = "((?P<group_name>[^/]+)/)?"

urlpatterns = patterns('',
    url(r"^%sformList$" % OPT_GROUP_REGEX, views.formList, name=FORM_LIST),
    url(r"^%ssubmission$" % OPT_GROUP_REGEX, views.submission),

    url(r"^%sxform/new/$" % OPT_GROUP_REGEX, views.create_xform),
    url(r"^%sxform/(?P<id_string>[^/]+)\.xml$" % OPT_GROUP_REGEX, views.download_xform, name=DOWNLOAD_XFORM),
    url(r"^xform/toggle_downloadable/(?P<id_string>[^/]+)/$", views.toggle_downloadable),
    url(r"^submission_test_form/?$", views.submission_test_form),
    url(r"^xform/(?P<id_string>[^/]+)/$", views.update_xform),
    url(r"^%s$" % OPT_GROUP_REGEX, views.list_xforms, name=LIST_XFORMS),
    url(r"^survey/(?P<pk>\d+)/$", views.instance),
)
