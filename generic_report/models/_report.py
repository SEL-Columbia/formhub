#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime
import eav

from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.db import models
from django.utils.datastructures import SortedDict
from django.db.models.signals import m2m_changed

from _indicator import SelectedIndicator, ValueIndicator, LocationIndicator


"""
    Reports (a group of data), report views (the way to display the data) and
    records (a batch of raw data). You may want to start with reports if 
    you are new to the code.
"""

# todo: remove start date and end dates and code and frenquency
# todo: add constraint to a report
class Report(models.Model):
    """
        Central object for this app, it is the link between all other 
        components. A report declare several indicators (see indicator.py) 
        and contains several data records. Views tell how to display 
        these records.
    """

    class Meta:
        verbose_name = __('report')
        app_label = 'generic_report'
        

    name = models.CharField(max_length=64, verbose_name=__(u'name'))

    @property
    def default_view(self):
        return self.views.get(name__iexact="default")
    

    def __unicode__(self):
        return _(u'%(name)s') % {'name': self.name}

    
    def get_stand_alone_indicators(self):
        """
            Return all indicators for this report that doesn't need any
            other indicators to exist.
        """
        
        sa_inds = ('valueindicator', 'dateindicator', 'locationindicator')
        indicators = self.indicators.all()
        return [i for i in indicators if i.strategy_type.model in sa_inds]
            


# todo: check that indicators are only from the report indicator
# todo: add indicator orders
class ReportView(models.Model):
    """
        A way to display the data of the report. Declare:
        
        - pagination (see paginator.py), meaning wich 
          portion of data you want to see. E.G: by batch of 10 records.
        - filtering (see filter.py), meaning which type of data you want to see.
          E.G: only data with value X < 45.
        - aggregation (see agregator.py), meaning how grouped you want the 
          data to be. E.G: grouped by date.
        - ordering (see orderer.py), meaning in which order you the data to
          appear. E.G: in alphabetical order.
    """

    class Meta:
        verbose_name = __('report view')
        verbose_name_plural = __('report views')
        unique_together = (('report', 'name'),)
        app_label = 'generic_report'
        

    report = models.ForeignKey(Report, related_name='views') 
    name = models.CharField(max_length=64, 
                            verbose_name=__(u'name'),
                            default=__('default'))
    time_format = models.CharField(max_length=32, 
                                   verbose_name=__(u'time format'),
                                   default='%m/%d/%Y',
                                   blank=True)  

   
    # todo: rework this part. Too many get_something_indicators. This is
    # neither efficient nor clear.

    def get_selected_indicators(self):
        """
            Return the indicators that must be displayed for this view:
            - get indicators from the selected indicator proxys
            - remove indicators that can not be displayed for this specific view
        """
        sis = self.selected_indicators.all().order_by('order')
        return [si.indicator for si in sis]


    def get_indicators(self):
        """
            Return all indicators, but with selected indicator ordered first
            so order is kept.
        """
        inds = self.get_selected_indicators()
        return inds + [i for i in self.report.indicators.all() if i not in inds]
        
    
    def get_numerical_indicators(self, queryset=None):  
        """
            Return indicators with INT or FLOAT concepts
        """
        indicators = queryset or self.get_indicators()
        types = (eav.models.Attribute.TYPE_INT, eav.models.Attribute.TYPE_FLOAT) 
        return [i for i in indicators if i.concept.datatype in types]


    # todo: add unit test for this
    def get_selectable_indicators(self, queryset=None):
        """
            Return the indicators that can be displayed for this view by
            removing indicators that can not be displayed for this specific view
        """
        
        indicators = queryset or self.get_indicators()
        
        # if there is an aggregation, remove non numeric indicators
        if self.aggregators.all().exists():
            aggregator = self.aggregators.all()[0]
            filtered_indicators = self.get_numerical_indicators(indicators)
            for indicator in indicators:
                if indicator.concept == aggregator.indicator.concept:
                   filtered_indicators.append(indicator)
            return filtered_indicators
        return indicators

    
    def get_indicators_to_display(self):
        """
            Filter selected indicators to get only the one we want and can 
            display
        """
        return self.get_selectable_indicators(self.get_selected_indicators())


    def get_labels(self):
        return [si.name for si in self.get_indicators_to_display()]
      
   
    def _create_data_grid(self):
        """
            Turn records into a list or sorted dicts
        """
        records = self.report.records.all()
        indicators = self.get_selectable_indicators()
        grid = [record.to_sorted_dict(indicators) for record in records]
        return indicators, grid
       
    
    def _update_grid_with_calculated_data(self, grid, indicators=None):
        """
            Fill the grid with data calculated from it.
            
            WARNING:
            
            This modifies the grid in place but return the grid for convenience.
        """
        # todo: optimise this to only call value indicator that calculate it
        indicators = indicators or self.get_selectable_indicators()
        for record in grid:
            for indic in indicators:
                record[indic.concept.slug] = indic.value(self, record) 
        return grid
                

    def _aggregate_data_grid(self, grid):
        """
            Fill the grid with data calculated from it
        """
        for aggregator in self.aggregators.all():
            grid = aggregator.get_aggregated_data(grid)
        return grid


    def _format_data_grid(self, grid, indicators=None):
        """
            Fill the grid with formated data, and removing data that is
            not meant to be displayed.
            
            WARNING:
            
            This modifies the grid in place but return the grid for convenience.
            
            You can't call update_grid_with_calulated_data() after it since 
            all values will be strings.
        """
        indicators = indicators or self.get_indicators_to_display()
        sis = SortedDict((i.concept.slug, i) for i in indicators)
        for record in grid:
            for key in record.keys():
                try:
                    record[key] = sis[key].format(self, record)
                except KeyError:
                    del record[key]
        return grid
        

    # cache that
    def get_data_grid(self):
    
        indicators, grid = self._create_data_grid()
         
        # Todo: cache this basic extraction, use it as a base for the other views
        self._update_grid_with_calculated_data(grid, indicators)

        grid = self._aggregate_data_grid(grid)

        # calculate the calculated indicators again so stuff like average get
        # it right
        self._update_grid_with_calculated_data(grid, indicators)
       
        # enventually, format the data 
        self._format_data_grid(grid)
        
        return grid
            
        
    def get_extracted_data(self):
        return []
       
       
    @classmethod
    def create_from_report(cls, report, name='Default'):
        """
            Create a view fromt the given report. The view will be attached
            to this report and reference the same indicators.
        """
        
        view = ReportView.objects.create(report=report, name=name)
        for ind in report.indicators.all():
            view.add_indicator(ind)
        return view
  
  
    # todo: create similar method for removing indicators
    def add_indicator(self, indicator, order=None):
        """
            Add an indicator to the current view. if it doesn't exists in 
            the associated report, add it to it too.
            Returns the ViewIndactor object responsible for the relation
            between the indicator and the view.
        """
        
        if indicator not in self.get_selected_indicators():
        
            vi = SelectedIndicator.objects.create(view=self, 
                                                  indicator=indicator, 
                                                  order=order)
           
            if indicator not in self.report.indicators.all():
                self.report.indicators.add(indicator)
            
            return vi
    
    
    def get_report_indicators_user_choices(self):
        """
            Return a dictionary mapping all indicators from this report
            to a boolean telling if it has been selected by the user to be 
            displayed in this view.
        """
        sis = self.selected_indicators.all()
        indicators = SortedDict(((si.indicator, True) for si in sis))
        for i in self.report.indicators.all():
            indicators[i] = indicators.get(i, False)
        return indicators
        
        
    def __unicode__(self):
        return _('View "%(view)s" of report "%(report)s"') % {
                 'view': self.name, 'report': self.report}


# todo: remove date and set that as an indicator automatically created
class Record(models.Model):
    """
        A batch of raw data. A record hold data using the django-eav app. 
        The app never access the report directly, each piece of data is 
        extracted from the record using an indicator objects (see indicator.py).
    """


    class Meta:
        verbose_name = __('record')
        verbose_name_plural = __('records')
        app_label = 'generic_report'


    date = models.DateField(default=datetime.datetime.today,
                                  verbose_name=__(u'date'))
    validated = models.BooleanField(default=False)
    report =  models.ForeignKey(Report, related_name='records') 
    
    def __unicode__(self):
        return _("Record %(record)s (sent on %(date)s) of report %(report)s") % {
                 'record': self.pk, 'report': self.report, 'date': self.date}

    def to_sorted_dict(self, indicators):
    
        data = SortedDict()
        for indicator in indicators:
            try:
                attr = indicator.concept.slug
                data[attr] = getattr(self.eav, attr)
            except AttributeError:
                pass
        return data


