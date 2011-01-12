#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import redirect_to
from django.core.urlresolvers import reverse

from generic_report.models import Report, ReportView

from generic_report_admin.forms import ReportForm, ViewForm


urlpatterns = patterns("",

    # Report CRUD URLs     
        
    url(r'report/create/$',  
        "django.views.generic.create_update.create_object",
        {"form_class": ReportForm, 
        "post_save_redirect": '/report/%(id)s/edit/defaultview/',
         "login_required": True, "template_name": "create_report.html"},
        name='create-report'),
  
    url(r'report/delete/(?P<object_id>\d+)/$',  
        "django.views.generic.create_update.delete_object",
        {"model": Report, "post_delete_redirect": 'dashboard',
         "login_required": True, "template_name": "delete_report.html",
         'template_object_name': 'report'},
        name='delete-report'),
 
    url(r'report/edit/(?P<object_id>\d+)/$',  
        "django.views.generic.create_update.update_object",
        {"model": Report, "post_save_redirect": '.',
         "login_required": True, "template_name": "edit_report.html",
         'template_object_name': 'report'},
        name='edit-report'), 

    url(r'report/(?P<id>\d+)/results/$',  
        "mangrove_demo.views.display_report", 
        name='report-results'),          

    url(r'reports/manage/$', 
        object_list, {'queryset': Report.objects.all(),
                       'template_name': 'report_list.html', 
                       'template_object_name': 'report'}, 
        name="reports-list"),
     
    url(r'report/(?P<id>\d+)/add/view/$',  
        "mangrove_demo.views.add_view_to_report", 
        name='add-view-to-report'), 

    url(r'report/(?P<id>\d+)/edit/defaultview/$',  
       "mangrove_demo.views.edit_default_view", 
        name='edit-default-view'),      
     
     
    # View CRUD URLs
        
    url(r'view/delete/(?P<id>\d+)/$',  
        "mangrove_demo.views.delete_view", 
        name='delete-view'), 

    url(r'view/(?P<object_id>\d+)/edit/settings/$',  
        "django.views.generic.create_update.update_object",
        {"form_class": ViewForm, "post_save_redirect": '.',
         "login_required": True, "template_name": "edit_view_settings.html",
         'template_object_name': 'view'},
        name='edit-view-settings'), 

    url(r'view/(?P<id>\d+)/edit/indicators/$',  
        "mangrove_demo.views.edit_view_indicators", 
        name='edit-view-indicators'), 
 
    url(r'view/(?P<id>\d+)/edit/aggregators/$',  
        "mangrove_demo.views.edit_view_aggregators",
        name='edit-view-aggregators'),       
        
    url(r'view/(?P<id>\d+)/edit/data-display/$',  
        "mangrove_demo.views.edit_view_data_display",
        name='edit-view-data-display'), 
   
        
    url(r'$',  redirect_to, { 'url': "/reports/manage/" }, name='dashboard')
)


