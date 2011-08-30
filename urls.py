from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from xform_manager import views as xform_manager_views
OPT_GROUP_REGEX = "((?P<group_name>[^/]+)/)?"

from main import views as main_views

from survey_photos.views import photo_redirect

urlpatterns = patterns('',
    url(r'^$', main_views.index),

    url(r'^xform_manager/', include('nmis.xform_manager.urls')),
    url(r"^%sformList$" % OPT_GROUP_REGEX, xform_manager_views.formList),
    url(r"^%ssubmission$" % OPT_GROUP_REGEX, xform_manager_views.submission),
    url(r'^xls2xform/', include('nmis.xls2xform.urls')),
    url(r'^main/', include('nmis.main.urls')),

    url(r'^survey_photos/(?P<size>\S+)/(?P<photo_id>\S+)$', photo_redirect),

    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
