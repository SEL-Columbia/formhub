#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
    Forms and tools to create and fill reports from generic_reports
"""

import itertools

from django import forms
from django.utils.safestring import mark_safe
from django.forms import ValidationError

import eav

from simple_locations.models import AreaType

from generic_report.models import (Indicator, ValueIndicator,
                                    LocationIndicator,
                                    RatioIndicator,
                                    RateIndicator,
                                    AverageIndicator, 
                                    SumIndicator, 
                                    ProductIndicator, 
                                    DifferenceIndicator, 
                                    DateIndicator)



class ValueIndicatorForm(forms.ModelForm):

    class Meta:
        model = ValueIndicator
        


class LocationIndicatorForm(forms.ModelForm):

    class Meta:
        model = LocationIndicator    
        
     
        
class RateIndicatorForm(forms.ModelForm):

    class Meta:
        model = RateIndicator 



class RatioIndicatorForm(forms.ModelForm):

    class Meta:
        model = RatioIndicator 



class AverageIndicatorForm(forms.ModelForm):

    class Meta:
        model = AverageIndicator 



class SumIndicatorForm(forms.ModelForm):

    class Meta:
        model = SumIndicator



class ProductIndicatorForm(forms.ModelForm):

    class Meta:
        model = ProductIndicator
        
        
        
class DateIndicatorForm(forms.ModelForm):

    class Meta:
        model = DateIndicator
        
        
class DifferenceIndicatorForm(forms.ModelForm):

    class Meta:
        model = DifferenceIndicator


class IndicatorCreationForm(forms.Form):
    """
        Create for to create an indicator and add it to a view. It will
        provide default values to the newly created indicators so you can
        safely edit it later.
        
        This is a simplified indicator creation: choose a type, choose a name,
        the rest is set by default and expect later edition.
    """


    TYPES_CHOICES = (("strings", "Letters and words (e.g: 'Steven' or 'X3Y')"),
                    ("integer", "Numbers (e.g: '34' or '1')"),
                    ("location", "Location (e.g: 'Nigeria' or 'Paris')"),
                    ("ratio", "Ratio between two numbers (e.g: 3 / 5)"),
                    ("rate", "Rate between two numbers (e.g: '80%')"),
                    ("average", "Average between several numbers"),
                    ("sum", "Sum (e.g: '87 + 34 + 76')"),
                    ("product", "Product (e.g: '87 X 34 X 76')"),
                    ("difference", "Difference of two numbers (e.g: '956 - 35')"),
                    ("date", "Date (e.g: '31-11-1985')"),)
                  
    
    name = forms.CharField(max_length=64, min_length=1)
    type = forms.ChoiceField(choices=TYPES_CHOICES)
    
    
    def __init__(self, report_view, *args, **kwargs):
        self.view = report_view
        forms.Form.__init__(self, *args, **kwargs)
        
                  
    def clean_name(self):
        name = self.cleaned_data['name']
        if eav.models.Attribute.objects.filter(name=name).exists():
            raise ValidationError('An indicator with this name already exists')
        return name
        

    def create_indicator(self, attr_type, ind_type):
        """
            Create any simple indicator indicator
        """
        return Indicator.create_with_attribute(self.cleaned_data['name'], 
                                                attr_type=attr_type, 
                                                indicator_type=ind_type)
                                                
    def create_location_indicator(self):
        """
            Create a location indicator with a default area type.
            If no area type, raise a ValidationError.
        """
        
        try:
            area_type = AreaType.objects.all()[0]
        except (AreaType.DoesNotExist, IndexError):
            raise ValidationError('You must create at least one area type '\
                                  'before using locations')
        
        return Indicator.create_with_attribute(self.cleaned_data['name'], 
                                    attr_type=eav.models.Attribute.TYPE_OBJECT, 
                                    indicator_type=LocationIndicator,
                                    kwargs={'area_type':area_type})
        
        
    def create_dividing_indicator(self, indicator_type):
        """
            Create a rate or a ratio indicator with default numerator and
            denominator.
            If there is not at least 2 numerical indicators in this view
            we can use as default parameters, raise a ValidationError.
        """
        
        indicators = self.view.get_numerical_indicators()
        
        if len(indicators) < 2:
            raise ValidationError('You need at least two other indicators '\
                                   'using numbers before creating this one')
        
        return Indicator.create_with_attribute(self.cleaned_data['name'], 
                                    attr_type=eav.models.Attribute.TYPE_FLOAT, 
                                    indicator_type=indicator_type,
                                    kwargs={'numerator': indicators[0],
                                            'denominator': indicators[1]})
 
 
    def create_indicator_with_params(self, indicator_type):
        """
            Create a any indicator that needs a numerical parameter
            If there is not at least 2 numerical indicators in this view
            we can use as default parameters, raise a ValidationError.
        """
        
        indicators = self.view.get_numerical_indicators()
        
        if not indicators:
            raise ValidationError('You need at least one other indicator '\
                                   'using number before creating this one')
        
        return Indicator.create_with_attribute(self.cleaned_data['name'], 
                                    attr_type=eav.models.Attribute.TYPE_FLOAT, 
                                    indicator_type=indicator_type,
                                    args=(indicators[0],))
 
 
    def create_difference_indicator(self):
        """
            Create a indicator substracting two default values.
            If there is not at least 2 numerical indicators in this view
            we can use as default parameters, raise a ValidationError.
        """
        
        indicators = self.view.get_numerical_indicators()
        
        if len(indicators) < 2:
            raise ValidationError('You have at least two other indicators '\
                                   'using numbers before creating this one')
        
        return Indicator.create_with_attribute(self.cleaned_data['name'], 
                                    attr_type=eav.models.Attribute.TYPE_FLOAT, 
                                    indicator_type=DifferenceIndicator,
                                    kwargs={'first_term': indicators[0],
                                            'term_to_substract': indicators[1]})
 
        
    def save(self, *args, **kwargs):
        """
            Create the proper indicator dynamically, by calling the factory
            function that matches its the 'type' argument.
        """
        mapping = dict(IndicatorCreationForm.TYPES_TO_FACTORIES)
        factory = mapping[self.cleaned_data['type']]
        return factory[0](self, *factory[1])


IndicatorCreationForm.TYPES_TO_FACTORIES = (
    ("string", (IndicatorCreationForm.create_indicator, 
                 (eav.models.Attribute.TYPE_TEXT, ValueIndicator))),
    ("number", (IndicatorCreationForm.create_indicator, 
                 (eav.models.Attribute.TYPE_FLOAT, ValueIndicator))),
    ("location", (IndicatorCreationForm.create_location_indicator, ())),
    ("ratio", (IndicatorCreationForm.create_dividing_indicator, 
               (RatioIndicator,))),
    ("rate", (IndicatorCreationForm.create_dividing_indicator, 
              (RateIndicator,))),
    ("average", (IndicatorCreationForm.create_indicator_with_params, 
                 (AverageIndicator,))),
    ("sum", (IndicatorCreationForm.create_indicator_with_params, 
             (SumIndicator,))),
    ("product", (IndicatorCreationForm.create_indicator_with_params, 
                 (ProductIndicator,))), 
    ("difference", (IndicatorCreationForm.create_difference_indicator, ())),
    ("date", (IndicatorCreationForm.create_indicator, 
              (eav.models.Attribute.TYPE_DATE, DateIndicator))),
)
                                   


class IndicatorChooserForm(forms.Form):
    """
        Choose a an indicator and add it to the current view.
    """


    def __init__(self, report_view, *args, **kwargs):
        self.view = report_view
        forms.Form.__init__(self, *args, **kwargs)

        to_remove = set(report_view.report.indicators.all())
        to_keep = set(Indicator.objects.all())
        self.indicators = list(to_keep.difference(to_remove))
        indicators = ((i.id, i.name) for i in self.indicators)
        self.fields['indicator'] = forms.ChoiceField(choices=indicators)
   

    def save(self, *args, **kwargs):
        indicator = Indicator.objects.get(pk=self.cleaned_data['indicator'])
        self.view.add_indicator(indicator)
        for ind in indicator.get_dependancies():
            self.view.add_indicator(ind)
        return indicator
                                  

class IndicatorEditionForm(forms.ModelForm):


    STRATEGIES_TO_FORMS = ((ValueIndicator, ValueIndicatorForm),
                            (LocationIndicator, LocationIndicatorForm),
                            (RatioIndicator, RatioIndicatorForm),
                            (RateIndicator, RateIndicatorForm),
                            (AverageIndicator, AverageIndicatorForm),
                            (SumIndicator, SumIndicatorForm),
                            (ProductIndicator, ProductIndicatorForm),
                            (DifferenceIndicator, DifferenceIndicatorForm),
                            (DateIndicator, DateIndicatorForm),)


    class Meta:
        model = Indicator
        exclude = ('strategy_type', 'strategy_id', 'report', 'concept')
        
        
    def __init__(self, *args, **kwargs):
    
        # choose the strategy form
        instance = kwargs.pop('instance', None)
        
        if not instance:
            raise ValueError('You must provide either the "instance" or the'\
                                 ' the "type parameter"')
        
        forms.ModelForm.__init__(self, instance=instance, *args, **kwargs)
        
        strat_mapping = dict(IndicatorEditionForm.STRATEGIES_TO_FORMS)
        strat_form_class = strat_mapping[instance.strategy.__class__]
        self.strategy_form = strat_form_class(instance=instance.strategy, 
                                              *args, **kwargs)


    def __unicode__(self):
        return mark_safe(forms.ModelForm.__unicode__(self) +\
                          unicode(self.strategy_form))
     
     
    def as_table(self):
        return mark_safe(forms.ModelForm.as_table(self) +\
                         self.strategy_form.as_table())


    def as_p(self):
        return mark_safe(forms.ModelForm.as_p(self) + '<div class="subform">' +\
                         self.strategy_form.as_p() + '</div>')

    def as_ul(self):
        return mark_safe(forms.ModelForm.as_ul(self) +\
                         self.strategy_form.as_ul())

    def __iter__(self):
        return itertools.chain(forms.ModelForm.__iter__(self),
                               iter(self.strategy_form))
        
    def is_valid(self):
        return forms.ModelForm.is_valid(self) and self.strategy_form.is_valid()
        
    # todo: put this in a transaction
    def save(self, *args, **kwargs):
        indicator = forms.ModelForm.save(self, *args, **kwargs) 
        self.strategy_form.save(*args, **kwargs)
        return indicator
        

class ViewIndicatorsForm(forms.Form):
    """
        Group all indicators forms as one form for an easy display / edition /
        saving.
        
        Couldn't manage to get formset working with this so it's done manually
        and may lack of some form features.
    """
        
    def __init__(self, report_view, *args, **kwargs):

        

        self.form_list = []
        for indicator in report_view.report.indicators.all():
            self.form_list.append(IndicatorEditionForm(instance=indicator,
                                                  prefix=indicator.concept.slug,
                                                  *args, **kwargs))
                                                  
        forms.Form.__init__(self, *args, **kwargs)
        
    def __unicode__(self):
        return mark_safe("".join(unicode(f) for f in self))
     
    def as_table(self):
        return mark_safe("".join(f.as_table() for f in self))

    def as_p(self):
        return mark_safe("".join(f.as_p() for f in self))

    def as_ul(self):
        return mark_safe("".join(f.as_ul for f in self))

    def __iter__(self):
        return iter(self.form_list)
        
    def is_valid(self):
        return forms.Form.is_valid(self) and all(f.is_valid for f in self.form_list)
        
        
    # todo: put this in a transaction
    def save(self, *args, **kwargs):
        return [f.save(*args, **kwargs) for f in self.form_list]
        indicator = forms.ModelForm.save(self) 
        return indicator
