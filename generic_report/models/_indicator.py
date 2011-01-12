#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
    List of classes used to define data types that composed a report.
    Indicator is the base class that uses all other indicator classes to 
    perform its job.
    One exception is Selected indicator, which is just a bridge between 
    indicators and report views.
"""

import eav.models
import operator

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import F

from simple_locations.models import AreaType


# todo: refactor selected_indictor to use the through param
class SelectedIndicator(models.Model):
    """
        Holder relationship between ReportView and Indicator.
        Used to be able to specify an order in indicators for views.
    """
    
    class Meta:
        app_label = 'generic_report'
        unique_together = (('view','indicator','order'),)
        ordering = ('order',)
        

    view = models.ForeignKey('generic_report.ReportView', 
                             related_name='selected_indicators')
    indicator = models.ForeignKey('Indicator', related_name='selected_for')
    order = models.IntegerField()
    
    def save(self, *args, **kwargs):
        
        # by default, create and order by incrementing the previous one,
        # or by setting it to 1 if no previous indicator exists for this view
        if self.order is None:
            try:
                siblings = SelectedIndicator.objects.filter(view=self.view)
                self.order = siblings.latest('order').order  + 1
            except SelectedIndicator.DoesNotExist:
                self.order = 1
        
        models.Model.save(self, *args, **kwargs)

    
    def increase_order(self):
        """
            If the current selected indicator is at the highest rank,
            increase it's rank of one, decreasing the rank of the first 
            indicator on top of it.
            
            Warning:
            - this method does't affect the other Python object
            attribute, therefor you must refresh your queryset as well
            when you use it.
            - this method increment the value of order in this object and in 
              the database but doesn't save the current object.
            
        """
        fresher_self = SelectedIndicator.objects.get(pk=self.pk)
        upper_indicators = self.view.selected_indicators.filter(order__gt=fresher_self.order)
        if upper_indicators:
            upper_indicator = upper_indicators[0]
            upper_indicator.order = fresher_self.order
            self.order = fresher_self.order = fresher_self.order + 1
            fresher_self.save()
            upper_indicator.save()
            

    def decrease_order(self):
        """
            If the current selected indicator is at the lowest rank,
            deacrease it's rank of one, increasing the rank of the first 
            indicator below it.
            
            Warning:
            - this method does't affect the other Python object
            attribute, therefor you must refresh your queryset as well
            when you use it.
            - this method increment the value of order in this object and in 
              the database but doesn't save the current object.
        """
        fresher_self = SelectedIndicator.objects.get(pk=self.pk)
        lower_indicators = self.view.selected_indicators.filter(order__lt=fresher_self.order)
        if lower_indicators:
            lower_indicator = tuple(lower_indicators)[-1]
            lower_indicator.order = fresher_self.order
            self.order = fresher_self.order = fresher_self.order - 1
            fresher_self.save()
            lower_indicator.save()
        

    def __unicode__(self):
        return "Selected indicator %(order)s for '%(view)s': %(indicator)s" % {
                'order': self.order, 'view': self.view, 
                'indicator': self.indicator}


# todo: remove parameter
class Parameter(models.Model):
    """
        Link between a calculated indicator and it's parameter.
        Gives an order.
    """
    
    class Meta:
        unique_together = (('param_of', 'indicator', 'order'))
        app_label = 'generic_report'
        
    
    param_of = models.ForeignKey('Indicator', related_name='params') 
    indicator = models.ForeignKey('Indicator', related_name='as_params') 
    order = models.IntegerField()
    
    def __unicode__(self):
        return "Param %s of %s" % (self.order, self.param_of)


# todo: add checks for parameter number
# todo: add checks for calculation dependancies
class Indicator(models.Model):
    """
        A type of value for the report. A report will have several indicator,
        which it will use to choose what kind of data to display.
        
        It extracts the corresponding
        value from each record, wether directly or by calculating it.
        
        The way to calculate the value depends of the indicator type.
        Each indicator type match a class wich contains the algo to extract
        the values. 
    """

    class Meta:
        verbose_name = __('indicator')
        app_label = 'generic_report'
        get_latest_by = 'id'


    # make it default to concept name
    name = models.CharField(max_length=64, verbose_name=__(u'name'))
    
    # todo: this field need a descritpion for south to freeze it
    concept = models.ForeignKey(eav.models.Attribute, blank=True)   

    report = models.ManyToManyField('generic_report.Report', 
                                    verbose_name=__(u'report'),
                                    related_name='indicators', 
                                    blank=True, null=True, symmetrical=False)

    # generic relation to a specialized indicator that will be used
    # to implement the strategy pattern 
    # we can't use the sub classes directly because they would be no way to
    # get all the indicators from the reports and views   
    strategy_type = models.ForeignKey(ContentType, null=True, blank=True)
    strategy_id = models.PositiveIntegerField(null=True, blank=True)
    strategy = generic.GenericForeignKey(ct_field="strategy_type", 
                                         fk_field="strategy_id")
        

    def __save__(self, *args, **kwargs):
        # you should not be able to change the type or the contept
        # after creating the indicator
        try:
            old_self = Indicator.objects.get(pk=self.pk)
            
            if self.concept != old_self.concept:
                raise IntegrityError(_("The concept can not be changed anymore"))
                
            if self.strategy != old_self.strategy:
                raise IntegrityError(_("The type can not be changed anymore"))
        except Indicator.DoesNotExist:
            pass
        models.Model.__save__(self, *args, **kwargs)
        
        
    def value(self, view, data):
        """
            Return the value of this indicator for this record, using the
            proper behavior according to the indicator type.
        """
        
        if not self.strategy:
            raise ValueError('Can not get value with an unsaved indicator')
        
        return self.strategy.value(view, data)


    def format(self, view, data):
        """
            Return the formated value of this indicator for this record, using 
            the proper behavior according to the indicator type.
        """
        
        if not self.strategy:
            raise ValueError('Can not format with an unsaved indicator')
        
        return self.strategy.format(view, data)    
    
    
    @classmethod
    def create_from_attribute(cls, attr, indicator_type=None, 
                              args=(), kwargs=None):
        """
            Create an indicator from the given EAV attribute. The indicator
            will be linked to this indicator and have the same name.
            
            By default, the indicator is a 'value' indicator. Pass type and
            a list of indicators as params to choose a different indicator type.
            Parameter order will be the same as the order of items in 'params'.
        """
        indicator_type = indicator_type or ValueIndicator 
        kwargs = kwargs or {}
         
        real_indicator = indicator_type.objects.create(**kwargs)
        
        # you must create the indicator proxy before adding a parameter
        # or it will fail
        ind = Indicator.objects.create(strategy=real_indicator, concept=attr, 
                               name=attr.name)

        # adding parameters. eventually they are added to the indicator proxy
        # anyway
        # todo: probably want to clean up the add_param that bounce from
        # one reference to another for no usefull reason
        for order, indicator in enumerate(args):
            real_indicator.add_param(indicator, order)

        return ind
        

    @classmethod
    def create_with_attribute(cls, name, attr_type=eav.models.Attribute.TYPE_INT, 
                              indicator_type=None, args=(), kwargs=None):
        """
            Create an indicator and the related EAV attribute. The indicator
            will be linked to this indicator wich will have the same name.
            
            This first attempts to create the attribute (to let the creation
            fail if it needs to) then it calls 'create_from_attribute' on it.
        """
        
        attr = eav.models.Attribute.objects.create(name=name, 
                                                   datatype=attr_type)
        return cls.create_from_attribute(attr, indicator_type, args, kwargs)
    
    
    def add_param(self, indicator, order=None):
        """
            Add the given indicator as a parameter of the current one. If no
            order is provided, the order will be calculated by taking the 
            highest parameter order for all params of this indicators and 
            adding 1.
            
            This method is delegated to the strategy.
        """
        return self.strategy.add_param(indicator, order)
  
  
    def get_dependancies(self):
        """
            Returns indicators required for this indicator to be calculated.
            
            This method is delegated to the strategy.
        """
        return self.strategy.get_dependancies()
  
     
    def __unicode__(self):
        return self.name



class IndicatorType(models.Model):
    """
        Common parent to all the specialized indicators that factor some
        behavior.
    """

    class Meta:
        app_label = 'generic_report'
    
    # todo: make proxy => _proxy and real 'proxy' an accessor
    proxy = generic.GenericRelation(Indicator, object_id_field="strategy_id",
                                    content_type_field="strategy_type")
    
    def format(self, view, data):
        # don't call value() here as you don't want calculation
        # calculation run between strings
    
        return unicode(data[self.proxy.all()[0].concept.slug])


    def value(self, view, data):
        """
            Return directly the value of this indicator in this data dict.
        """
        
        # if it's a record object, turn it into a sorted dict
        if hasattr(data, 'to_sorted_dict'):
            data = data.to_sorted_dict(view.get_selected_indicators())
        
        return data[self.proxy.all()[0].concept.slug]
    
    
    def add_param(self, indicator, order=None):
        """
            Add the given indicator as a parameter of the current one. If no
            order is provided, the order will be calculated by taking the 
            highest parameter order for all params of this indicators and 
            adding 1.
        """
        # todo : move the param order check in param
        if order is None :
            try:
                order = self.proxy.all()[0].params.latest('order').order  + 1
            except Parameter.DoesNotExist:
                order = 1
        
        return Parameter.objects.create(param_of=self.proxy.all()[0], 
                                        indicator=indicator, 
                                        order=order)

    def get_dependancies(self):
        """
            Returns indicator declared as parameters
        """
        proxy = self.proxy.all()[0]
        return [p.indicator for p in Parameter.objects.filter(param_of=proxy)]
        
        
    
    def __unicode__(self):
        try:
            proxy = self.proxy.latest()
        except Indicator.DoesNotExist:
            proxy = 'unknown'
        return "Indicator type of indicator '%(indicator)s'" % {
                'indicator': proxy}

        

class ValueIndicator(IndicatorType):

    class Meta:
        app_label = 'generic_report'
        verbose_name = __("Value Indicator")
        verbose_name_plural = __("Value Indicators")


class LocationIndicator(IndicatorType):
    """
        Indicator strategy expecting a Django model object in the EAV value.
        
        The model for now is strongly coupled with the application 
        simple_location and therefor should be an AreaType object.
    """
    
    class Meta:
        app_label = 'generic_report'
        verbose_name = __("Location Indicator")
        verbose_name_plural = __("Location Indicators")
        
    area_type = models.ForeignKey(AreaType, related_name='type_of')



# todo: add checks on indicator parameters type (can't sum a district)
# todo: merge with rate indicator
class RatioIndicator(IndicatorType): 
    """
        Indicator strategy dividing two EAV values from two indicators.
    """
    
    class Meta:
        app_label = 'generic_report'
        
    numerator = models.ForeignKey(Indicator, 
                                  related_name='numerator_of_ratio')
    denominator = models.ForeignKey(Indicator, 
                                    related_name='denominator_of_ratio')

    # todo: add checks for ratio to accept 2 and only two args
    def value(self, view, data):
        """
            Return a ratio between the values of the 2 indicators in this
            record.
        """
        val = operator.truediv(self.numerator.value(view, data), 
                               self.denominator.value(view, data))
        return round(val, 2)


    def get_dependancies(self):
        """
            Returns numerator and denominator
        """
        return [self.numerator, self.denominator]



# todo: add rate formating in the view
class RateIndicator(IndicatorType): 
    """
        Indicator strategy dividing two EAV values from two indicators and then
        make it a pourcentage (%).
    """
    
    class Meta:
        app_label = 'generic_report'

    numerator = models.ForeignKey(Indicator, related_name='numerator_of_rate')
    denominator = models.ForeignKey(Indicator, related_name='denominator_of_rate')

    # todo: add checks for rate to accept 2 and only two args
    def value(self, view, data):
        """
            Return a rate between the values of the 2 indicators in this
            record.
        """
        val = operator.truediv(self.numerator.value(view, data), 
                               self.denominator.value(view, data))
        return round(val * 100, 2)


    def format(self, view, data):
        """
            Return the rate with a "%" sign
        """
        return "%s %%" % data[self.proxy.all()[0].concept.slug]


    def get_dependancies(self):
        """
            Returns numerator and denominator
        """
        return [self.numerator, self.denominator]


class AverageIndicator(IndicatorType): 
    """
        Indicator strategy calculating the average of several EAV values 
        from several indicators.
    """
    
    class Meta:
        app_label = 'generic_report'
        
    def value(self, view, data):
        """
            Return the average of the values for these indicators in this
            record.
        """
        parameters = self.proxy.all()[0].params.all().order_by('order')
        values = [param.indicator.value(view, data) for param in parameters]
        return round(operator.truediv(sum(values), len(values)), 2)  



class SumIndicator(IndicatorType): 
    """
        Indicator strategy summing several EAV values from several indicators.
    """
    
    class Meta:
        app_label = 'generic_report'

    def value(self, view, data):
        """
            Return the sum of the values for these indicators in this
            record.
        """
        parameters = self.proxy.all()[0].params.all().order_by('order')
        return sum(param.indicator.value(view, data) for param in parameters)



class ProductIndicator(IndicatorType): 
    """
        Indicator strategy multiplying several EAV values
        from several indicators.
    """
    
    class Meta:
        app_label = 'generic_report'

    def value(self, view, data):
        """
            Return the product of the values for these indicators in this
            record.
        """
        parameters = self.proxy.all()[0].params.all().order_by('order')
        return reduce(operator.mul, 
                     (param.indicator.value(view, data) for param in parameters))


# todo: check parameters: you can't subtract non numeric values
class DifferenceIndicator(IndicatorType): 
    """
        Indicator strategy substracting two EAV values from two indicators.
    """
    
    class Meta:
        app_label = 'generic_report'
        
    first_term = models.ForeignKey(Indicator, related_name='first_term_of')
    term_to_substract = models.ForeignKey(Indicator, 
                                          related_name='term_to_substract_of')

    def value(self, view, data):
        """
            Return the difference of the values for these indicators in this
            record.
        """
        return self.first_term.value(view, data) -\
               self.term_to_substract.value(view, data)


    def get_dependancies(self):
        """
            Returns first_term and term_to_substract 
        """
        return [self.first_term, self.term_to_substract ]        
        


class DateIndicator(IndicatorType): 
    """
        Indicator strategy expecting a Python date object in the EAV value.
    """

    class Meta:
        app_label = 'generic_report'
        verbose_name = __("Date Indicator")
        verbose_name_plural = __("Date Indicators")
        
        
    # todo: make format more efficient        
    def format(self, view, data):
        """
            Return a date according to the view format or any aggregator format.
        """
        indicator = self.proxy.all()[0]
        date = self.value(view, data)

        if not date:
            return None

        if view.aggregators.all().exists():
            aggregator = view.aggregators.all()[0]
            if aggregator.indicator == indicator:
                return aggregator.format(date)

        return date.strftime(view.time_format)
