from django.conf.urls.defaults import patterns, url

import views

urlpatterns = patterns(
    '',
    url(r'^requests.html$', views.user_request_counts),
    )
