from datetime import datetime

from django.test import TestCase
from django import forms

from generic_report.models import *
from generic_report_admin.forms import *
from eav.models import *

eav.register(Record)

class RecordFormsTests(TestCase):

    """
        Testing report filling using forms.
    """


    def setUp(self):
        self.report = Report.objects.create(name='Square')
        self.height = Attribute.objects.create(name='Height', 
                                               datatype=Attribute.TYPE_INT)
        self.height_indicator = Indicator.create_from_attribute(self.height)

        self.width = Attribute.objects.create(name='Width', 
                                               datatype=Attribute.TYPE_INT)
        self.width_indicator = Indicator.create_from_attribute(self.width)

        self.report.indicators.add(self.height_indicator)
        self.report.indicators.add(self.width_indicator)
        
        self.view = ReportView.create_from_report(report=self.report, 
                                                  name='main')
        
        self.record = Record.objects.create(report=self.report)
        self.record.eav.height = 10
        self.record.eav.width = 2
        self.record.save()
        
        

    def test_form_creation(self):
        rf = RecordForm(report=self.report)

        # this should not be in base fields as it is a calculated indicator
        i = Indicator.create_with_attribute('i', 
                                             Attribute.TYPE_INT,
                                             SumIndicator,
                                             (self.height_indicator, 
                                              self.width_indicator))
        
        self.assertEqual(rf.__class__.__name__, 'SquareRecordForm')
        self.assertEqual(sorted(rf.base_fields.keys()), ['height', 'width'])
 
 
    def test_basic_validation(self):
    
        rf = RecordForm({'width':5, 'height':3}, report=self.report)
        self.assertTrue(rf.is_valid())
        rf = RecordForm({'width':5,}, report=self.report)
        self.assertFalse(rf.is_valid())
        
        
    def test_saving_record_form_create_a_record(self):
        self.assertEqual(self.report.records.count(), 1)
        
        rf = RecordForm({'width':5, 'height':3}, report=self.report)
        rf.is_valid()
        record = rf.save()
        
        self.assertEqual(self.report.records.count(), 2)
        self.assertEqual(record.eav.height, 3)
        self.assertEqual(record.eav.width, 5)
        
        
    def test_all_data_types(self):
    
        r = Report.objects.create(name='r')
        
        t_int = Indicator.create_with_attribute('t_int')
        t_float = Indicator.create_with_attribute('t_float', 
                                                  Attribute.TYPE_FLOAT, 
                                                  ValueIndicator)
        t_text = Indicator.create_with_attribute('t_text', 
                                                  Attribute.TYPE_TEXT, 
                                                  ValueIndicator)
        t_date = Indicator.create_with_attribute('t_date', 
                                                  Attribute.TYPE_DATE, 
                                                  ValueIndicator)  
        t_bool = Indicator.create_with_attribute('t_bool', 
                                                  Attribute.TYPE_BOOLEAN, 
                                                  ValueIndicator) 
                   
        at = AreaType.objects.create(name='City')                              
        t_location = Indicator.create_with_attribute('t_location', 
                                                     Attribute.TYPE_OBJECT, 
                                                     LocationIndicator,
                                                     kwargs={'area_type':at})                                                      
                                                                                                  
        r.indicators.add(t_int)
        r.indicators.add(t_float)
        r.indicators.add(t_text)
        r.indicators.add(t_date)
        r.indicators.add(t_bool)
        r.indicators.add(t_location)

        rf = RecordForm(report=r)

        self.assertEqual(rf.base_fields['t_int'].__class__, forms.IntegerField)        
        self.assertEqual(rf.base_fields['t_float'].__class__, forms.FloatField)  
        self.assertEqual(rf.base_fields['t_text'].__class__, forms.CharField)  
        self.assertEqual(rf.base_fields['t_date'].__class__, forms.DateField)  
        self.assertEqual(rf.base_fields['t_bool'].__class__, forms.BooleanField)
        self.assertEqual(rf.base_fields['t_location'].__class__, forms.ModelChoiceField)   

