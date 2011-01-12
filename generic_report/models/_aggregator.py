#!/usr/bin/env python
# encoding=utf-8
# vim: ai ts=4 sts=4 et sw=4

"""
    Classes that labels values from records and group data according to this
    labels, summing numerical data and hidding non numerical data.
    Act like an SQL 'GROUP BY' but for data matrices generated from reports.
"""

import datetime

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.datastructures import SortedDict

from simple_locations.models import AreaType


class Aggregator(models.Model):
    """
            A logic process to group data around one value of the report.
            A report can have several aggregators but it's not mandatory.
            
            It extracts the corresponding
            value from each record, wether directly or by calculating it.
            
            Aggregators are only linked to view, as they are just a way to
            present the data.
            
            The way to dispatch values depends of the aggregator type.
            Each aggregator type match a class wich contains the algo to dispatch
            the values. All these classes are in the '_indicator.py' file.
    """

    class Meta:
        verbose_name = __('aggregator')
        verbose_name_plural = __('aggregators')
        app_label = 'generic_report'
        get_latest_by = 'id'

    # todo: add check to ensure the indicator is in the selected indicator
    # of this view
    view = models.ForeignKey('generic_report.ReportView', 
                            verbose_name=__(u'view'),
                            related_name='aggregators')
                            
    indicator = models.ForeignKey('generic_report.Indicator', 
                            verbose_name=__(u'indicator'),
                            related_name='aggregators')

    # generic relation to a specialized aggregator that will be used
    # to implement the strategy pattern 
    # we can't use the sub classes directly because they would be no way to
    # get all the aggregators from the reports and views   
    strategy_type = models.ForeignKey(ContentType, null=True, blank=True)
    strategy_id = models.PositiveIntegerField(null=True, blank=True)
    strategy = generic.GenericForeignKey(ct_field="strategy_type", 
                                         fk_field="strategy_id")
        

    def get_aggregated_data(self, matrice):
        """
            Return the aggregated this matriced with the data grouped according
            to the algo the strategy class.
        """
        return self.strategy.get_aggregated_data(matrice)


    def format(self, value):
        """
            Return the aggregated value formated according to the type
            of aggregation.
        """
        return self.strategy.format(value)


    def filter(self, value):
        """
            Return if the value can be kept or not for display. Some value
            are not valid for the current aggregation (e.g: a country when
            you are aggregating by state).
            
            Returns True if you can keep it, or False if you need to skip it.
        """
        return self.strategy.filter(value)


    def __save__(self, *args, **kwargs):
        # you should not be able to change the type or the aggregator
        # after creating the aggregator
        try:
            old_self = Indicator.objects.get(pk=self.pk)
            
            if self.strategy != old_self.strategy:
                raise IntegrityError(_("The type can not be changed anymore"))
        except Indicator.DoesNotExist:
            pass
        models.Model.__save__(self, *args, **kwargs)
       
    
    def __unicode__(self):
        return _("Aggregator of view %(view)s") % {'view': self.view}



class AggregatorType(models.Model):
    """
        Common parent to all the specialized aggregator that factor some
        behavior.
    """

    class Meta:
        app_label = 'generic_report'
    
    proxy = generic.GenericRelation(Aggregator, object_id_field="strategy_id",
                                    content_type_field="strategy_type")
    
    def get_aggregated_data(self, matrice):
        """
            Return an aggregated matrice with the data grouped around the 
            values related to the linked indicator.
        """
        
        new_matrice = {}
        proxy = self.proxy.latest()
        indicator = proxy.indicator
        slug = indicator.concept.slug
        view = proxy.view
        
        # aggregate the matrice
        for data in matrice:
            ref_value = indicator.value(view, data)
            
            # filter the data, excluding impossible to aggregate data
            if not self.filter(ref_value):
                continue
            
            aggreated_ref_value = self.get_aggregated_value(ref_value)
            
            new_data = new_matrice.setdefault(aggreated_ref_value, SortedDict())
            
            for name, value in data.iteritems():
                print name, value
                if name == slug:
                    new_data[slug] = aggreated_ref_value
                else:
                    new = new_data.get(name, 0)
                    # if an indicator is added later, they will be None values
                    if value == None or new == None:
                        new_data[name] = None   
                    else:
                        new_data[name] = new_data.get(name, 0) + value
         
        # reformat it the way it was
        return [value for key, value in new_matrice.iteritems()]


    def format(self, value):
        """
            Format the value after it has been agregated (it can change since
            the data may not be the same type. e.g.: date -> month)
        """
        return unicode(value)    
    

    def filter(self, value):
        """
            Return if the value can be kept or not for display. Some value
            are not valid for the current aggregation (e.g: a country when
            you are aggregating by state). 
            
            This one always returns True.
        """
        return True

    
    def __unicode__(self):
        try:
            proxy = self.proxy.latest()
        except Aggregator.DoesNotExist:
            proxy = 'unknown'
        return "Aggregator type of aggregator '%(aggregator)s'" % {
                'aggregator': proxy}
                
                
class DateAggregator(AggregatorType): 
    """
        Aggregate by period of time: days, weeks, months or years.
    """

    class Meta:
        app_label = 'generic_report'
        

    TIME_PERIOD_CHOISES = (('day', __('Day')),
                           ('week', __('Week')),
                           ('month', __('Month')),
                           ('year', __('Year')),)    

    time_period = models.CharField(max_length=10, default='month',
                                   choices=TIME_PERIOD_CHOISES,
                                   verbose_name=__(u'time period'))

    # todo: add number_of_period

    def __init__(self, *args, **kwargs):
        AggregatorType.__init__(self, *args, **kwargs)
        
        aggregations_strategies = dict(DateAggregator.AGGREGATION_STRATEGIES)
        self.aggregation_strategy = aggregations_strategies[self.time_period]
        
        formating_strategies = dict(DateAggregator.FORMATING_STRATEGIES)
        self.formating_strategy = formating_strategies[self.time_period]


    def get_aggregated_value(self, date):
        """
            Return the value, as an integer representing the day, month,
            week or year, according to the choosen time period for
            aggregation.
        """
        return self.aggregation_strategy(date)
    
    
    def format(self, value):
        """
            Return the value, as a verbose string representing the 
            part of the date the value has been reduced to.
        """
        return self.formating_strategy(value)
    
    
    @classmethod
    def aggregate_by_day(cls, date):
        return date
    

    @classmethod
    def aggregate_by_month(cls, date):
        return (date.month, date.year)


    @classmethod
    def aggregate_by_week(cls, date):
        return (date.isocalendar()[1], date.year)     
 
 
    @classmethod
    def aggregate_by_year(cls, date):
        return date.year
    

    @classmethod
    def format_day(cls, date):
        return format(date, "M dS, Y") # use the django format function
    

    @classmethod
    def format_month(cls, value):
        d = datetime.date(value[1], value[0], 1)
        return d.strftime('%B, %Y')


    # todo: make configurable the first day of the week (sunday / monday)
    @classmethod
    def format_week(cls, value):
        return _('Week %(week)s of %(year)s') % {
               'week': value[0], 'year': value[1]}
 
 
    @classmethod
    def format_year(cls, year):
        return unicode(year) 

    
DateAggregator.AGGREGATION_STRATEGIES = (('day', DateAggregator.aggregate_by_day),
                                         ('week', DateAggregator.aggregate_by_week),
                                         ('month', DateAggregator.aggregate_by_month),
                                         ('year', DateAggregator.aggregate_by_year),)  
                                             
DateAggregator.FORMATING_STRATEGIES = (('day', DateAggregator.format_day),
                                     ('week', DateAggregator.format_week),
                                     ('month', DateAggregator.format_month),
                                     ('year', DateAggregator.format_year),) 
                                     
                                    
                                     
class LocationAggregator(AggregatorType): 
    """
        Aggregate by place type. Everything that is this type or IN a place
        with this type will be grouped.
    """

    class Meta:
        app_label = 'generic_report'
        

    area_type = models.ForeignKey(AreaType, 
                                  verbose_name=__(u'Area Type'),
                                  related_name='agregated_by')

    def __init__(self, *args, **kwargs):
        AggregatorType.__init__(self, *args, **kwargs)
        if not self.area_type_id:
            try:
               self.area_type = AreaType.objects.all()[0]
            except AreaType.DoesNotExist:
                pass


    # todo: make a filter method : e.g. if you aggregate by district, remove countries
    def get_aggregated_value(self, location):
        """
            Return the location object which is the common parent
        """
        
        return self.get_closest_matching_location_with_type(location)
        
        
    def get_closest_matching_location_with_type(self, location):
        """
            Return the location object which is the common parent or None
            if it doesn't exist.
        """
        
        # todo: ensure in simple location that you can't make an infinite 
        # reference loop
        
        while 1:
        
            if location.kind == self.area_type:
                return location
                
            location = location.parent
            
            if not location:
                return None
     
     
    def filter(self, location):
        """
            Return False if the area does not match the area type, nor does
            any of its parent
        """
        return bool(self.get_closest_matching_location_with_type(location))   
        
        
class ValueAggregator(AggregatorType): 
    """
        Aggregate values. Returns the value 'as is'.
    """

    class Meta:
        app_label = 'generic_report'
        


    def get_aggregated_value(self, value):
        """
            Return the location object which is the common parent
        """
        
        return value
        
     
 
