from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import views

urlpatterns = patterns(
    '',
    url(r'^facility/(?P<facility_id>[^/]+)/$', views.facility),
    url(r'^site/(?P<site_id>\S+)$', views.facilities_for_site),
    url(r'^$', views.home, name='home'),
    url(r'^data_dictionary/$', views.data_dictionary),
    url(r'^boolean_counts_for_facilities_in_lga/(?P<lga_id>[^/]+)/$', \
        views.boolean_counts_for_facilities_in_lga),
    )
