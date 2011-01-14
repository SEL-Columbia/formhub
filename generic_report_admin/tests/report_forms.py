from datetime import datetime

from django.test import TestCase
from django import forms

from generic_report.models import *
from generic_report_admin.forms import *
from eav.models import *

eav.register(Record)

class ReportFormsTests(TestCase):

    """
        Testing report basics such as reports creation, views, indicators, etc.
    """


    def setUp(self):
        pass
        

    def test_form_creation(self):
    
        form = ReportForm({'name':"test"})
        
        self.assertTrue(form.is_valid())
        
        form.save()
        
        report = Report.objects.get(name="test")
        self.assertEqual(report.name, 'test')
        
        self.assertEqual(report.views.count(), 1)
        self.assertEqual(report.views.all()[0].name, 'Default')
 
 

