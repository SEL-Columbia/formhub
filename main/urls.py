from django.conf.urls.defaults import patterns, url
import views

urlpatterns = patterns('',
    url(r'^$', views.dashboard),
    url(r'^tutorial/$', views.tutorial),
    url(r'^support/$', views.support),
    url(r'^syntax/$', views.syntax),
    url(r'^gallery/$', views.gallery),
)
