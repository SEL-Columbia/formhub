#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
    Forms and tools to create and edit views  from generic_reports
"""

from django import forms
from django.template.defaultfilters import slugify

from generic_report.models import *


class LocationAggregatorForm(forms.ModelForm):
    class Meta:
        model = LocationAggregator
        
class ValueAggregatorForm(forms.ModelForm):
    class Meta:
        model = ValueAggregator
        
class DateAggregatorForm(forms.ModelForm):
    class Meta:
        model = DateAggregator    


class ViewForm(forms.ModelForm):
    """
        Just create a view
    """
    
    class Meta:
        model = ReportView
        exclude = ('report',)


class ViewAggregationFormBase(forms.Form):
    """
        Base class for aggration management forms that we create on the fly.
        
        Not meant to be instanciated directly, use ViewAggregationForm instead.
    """
    
    INDICATORS_TO_AGGREGATORS = ((ValueIndicator, ValueAggregator),
                                (LocationIndicator, LocationAggregator),
                                (RatioIndicator, ValueAggregator), 
                                (RateIndicator, ValueAggregator), 
                                (AverageIndicator, ValueAggregator), 
                                (SumIndicator, ValueAggregator), 
                                (ProductIndicator, ValueAggregator), 
                                (DifferenceIndicator, ValueAggregator), 
                                (DateIndicator, DateAggregator))

    
    AGGREGATORS_TO_FORMS = ((LocationAggregator, LocationAggregatorForm),
                            (ValueAggregator, ValueAggregatorForm), 
                            (DateAggregator, DateAggregatorForm))
    
    
    def __init__(self, *args, **kwargs):
        self.view = kwargs.pop('view')
        forms.Form.__init__(self, *args, **kwargs)
        

    def is_valid(self):
        # this is an ugly hack to get the option form to validate. sorry
        if self.options:
            self.options = self.options.__class__(self.data, instance=self.options.instance)
            return forms.Form.is_valid(self) and self.options.is_valid()
        return forms.Form.is_valid(self)

        
    def save(self, instance=None, *args, **kwargs):
        # todo: check that this indicator belong to this view
        
        Aggregator.objects.filter(view=self.view).delete()
        try:
            pk = self.cleaned_data['aggregate_by']
            indicator = Indicator.objects.get(pk=pk)
        except Indicator.DoesNotExist:
            pass    
        else:
            indicator_type = indicator.strategy.__class__
            mapping = dict(ViewAggregationFormBase.INDICATORS_TO_AGGREGATORS)
            aggregator_strat = mapping[indicator_type]
            a = Aggregator.objects.create(view=self.view, indicator=indicator,
                                      strategy=aggregator_strat.objects.create())
            if self.options:
                self.options.instance.id = a.strategy.id
                self.options.save()


class ViewAggregationForm(forms.Form):
    """
        Factory to create ViewAggregationForms on the fly.
    """
    
    @classmethod
    def get_form(cls, view):
        """
            List all indicators in the view and make a choice list with it
        """
        
        report = view.report
        
        form_name = ("%s%s%s" % (slugify(report.name).title(), 
                                 slugify(view.name).title(), 
                                'ViewAggregationForm')).encode('ascii')
        
        # create the indicators select field                      
        indicators = [(i.pk, i.name) for i in report.indicators.all()]
        indicators += [(0, 'None of them'),] 
        
        try:
            aggregator = Aggregator.objects.get(view=view)
            initial = aggregator.indicator.pk
        except Aggregator.DoesNotExist:
            initial = aggregator = 0
        
        fields = {'aggregate_by': forms.ChoiceField(widget=forms.RadioSelect,
                                                    choices=indicators,
                                                    initial=initial),
                  'INDICATOR_CHOICES': indicators}
        
        # create the option form, according to the indicator
        if aggregator:
             aggregator_strat = aggregator.strategy.__class__
             mapping = dict(ViewAggregationFormBase.AGGREGATORS_TO_FORMS)
             fields['options'] = mapping[aggregator_strat](instance=aggregator.strategy)
        else:
             fields['options'] = None
                 
        return type(form_name, (ViewAggregationFormBase,), fields)
    
    
    def __new__(cls, *args, **kwargs):
        """
            Create the proper form according to the view then instanciate
            the form with the proper args
        """
    
        try:
            view = kwargs['view']
        except KeyError:
            raise TypeError('You must provide "view" as a keyword argument')

        return cls.get_form(view)(*args, **kwargs)
        

            
