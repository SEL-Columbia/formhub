#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
    Forms and tools to create and fill reports from generic_reports
"""

from django import forms
from django.template.defaultfilters import slugify

from simple_locations.models import Area

from generic_report.models import Record, ValueIndicator, Report, ReportView


class ReportForm(forms.ModelForm):
    """
        Just create a report
    """
    
    class Meta:
        model = Report
    
    def save(*args, **kwargs):
        
        report = forms.ModelForm.save(*args, **kwargs)
        
        # always provide a report with a default view
        if not report.views.exists():
            ReportView.create_from_report(report)
            
        return report



class RecordFormBase(forms.Form):
    """
        Base class for report filler forms that we create on the fly.
        
        Not meant to be instanciated directly, use RecordForm instead.
    """
    
    def __init__(self, *args, **kwargs):
        self.report = kwargs.pop('report')
        forms.Form.__init__(self, *args, **kwargs)
        
    
    
    def save(self, instance=None, *args, **kwargs):
        record = instance or Record(report=self.report)
        for name, data in self.cleaned_data.iteritems():
            setattr(record.eav, name, data)
        record.save()
        return record



class RecordForm(forms.Form):
    """
        Factory to create report form on the fly.
    """
    
    CONCEPT_TYPE_TO_FORM_FIELDS = (('text', forms.CharField),
                                   ('float', forms.FloatField),
                                   ('int', forms.IntegerField),
                                   ('date', forms.DateField),
                                   ('bool', forms.BooleanField),)
    
    @classmethod
    def get_form(cls, report):
        """
            Take all indicators that don't need other indicators to be 
            calculated, then create a form field that can accept the value
            for each of them.
        """
        
        mapping = dict(cls.CONCEPT_TYPE_TO_FORM_FIELDS)
        form_name = (slugify(report.name).title() + 'RecordForm').encode('ascii')
        fields = {}
        
        for indicator in report.get_stand_alone_indicators():
        
            if indicator.strategy_type.model in ('valueindicator, dateindicator'):
                field = mapping[indicator.concept.datatype]()
            else:
                locations = Area.objects.filter(kind=indicator.strategy.area_type)
                field = forms.ModelChoiceField(queryset=locations)
            
            fields[indicator.concept.slug] = field
            
        return type(form_name, (RecordFormBase,), fields)
    
    
    def __new__(cls, *args, **kwargs):
        """
            Create the proper form according to the report then instanciate
            the form with the proper args
        """
    
        try:
            report = kwargs['report']
        except KeyError:
            raise TypeError('You must provide "report" as a keyword argument')

        return cls.get_form(report)(*args, **kwargs)
        



