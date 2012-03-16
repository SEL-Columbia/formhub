from django.conf.urls.defaults import patterns, include, url
from main.google_export import google_oauth2_request
from main.google_export import google_auth_return

urlpatterns = patterns('',
    url(r'^gauthtest$',
        google_oauth2_request,
        name='google-auth'),
    url(r'^gwelcome$',
        google_auth_return,
        name='google-auth-welcome'),
)