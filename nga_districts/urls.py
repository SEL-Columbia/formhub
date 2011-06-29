from django.conf.urls.defaults import patterns, url
import views

urlpatterns = patterns(
    '',
    url(r'^lga_data/(?P<lga_id>[^/]+)/$', views.lga_data),
    )
