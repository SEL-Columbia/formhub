from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^(?P<site_id>\S+)$', 'facilities.views.facilities_for_site', name='facilities_for_site'),
    url(r'^$', 'facilities.views.home', name='home'),
)