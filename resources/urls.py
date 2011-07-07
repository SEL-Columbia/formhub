from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import views

urlpatterns = patterns(
    '',
    url(r'^$', views.resources),
    )
