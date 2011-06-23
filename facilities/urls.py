from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import views

urlpatterns = patterns(
    '',
    url(r'^facility/(?P<facility_id>[^/+])/$', views.facility),
    url(r'^(?P<site_id>\S+)$', views.facilities_for_site),
    url(r'^$', views.home, name='home'),
    )
