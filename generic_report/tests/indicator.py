from datetime import datetime

from django.test import TestCase

from ..models import *
from eav.models import *

eav.register(Record)

class IndicatorTests(TestCase):

    """
        Testing all types of indicators
    """
 

    def setUp(self):
    
        self.report = Report.objects.create(name='Test')
        
        self.a = Indicator.create_with_attribute('A')
        self.b = Indicator.create_with_attribute('B')
        self.c = Indicator.create_with_attribute('C')

        self.report.indicators.add(self.a)
        self.report.indicators.add(self.b)
        self.report.indicators.add(self.c)
        
        self.view = ReportView.create_from_report(report=self.report)
        
        self.record = Record.objects.get_or_create(report=self.report)
        self.record.eav.a = 10
        self.record.eav.b = 2
        self.record.eav.c = 3
        
        self.record.save()
        

    def tearDown(self):
        pass


    def test_value_indicator(self):
    
       value = self.a.value(self.view, self.record)
       self.assertEqual(value, 10)
       
       data = self.record.to_sorted_dict(self.view.get_selected_indicators())
       formated_value = self.a.format(self.view, data)
       self.assertEqual(formated_value , '10')
   
   
    def test_sum_indicator(self):
    
        i = Indicator.create_with_attribute('D', Attribute.TYPE_INT, 
                                            SumIndicator, 
                                            (self.a, self.b, self.c))
                                                        
        self.view.add_indicator(i)
    
        value = i.value(self.view, self.record)
        self.assertEqual(value, 15)  
        
        grid = self.view._create_data_grid()[1]
        self.view._update_grid_with_calculated_data(grid)
        
        formated_value = i.format(self.view, grid[0])
        
        self.assertEqual(formated_value , '15')
       
 
    def test_product_indicator(self):
    
        i = Indicator.create_with_attribute('D', Attribute.TYPE_INT, 
                                            ProductIndicator, 
                                            (self.a, self.b, self.c))

        self.view.add_indicator(i)

        value = i.value(self.view, self.record)
        self.assertEqual(value, 60)  
        
        grid = self.view._create_data_grid()[1]
        self.view._update_grid_with_calculated_data(grid)
        
        formated_value = i.format(self.view, grid[0])
        
        self.assertEqual(formated_value , '60')
        
        
        
    def test_ratio_indicator(self):
    
        i = Indicator.create_with_attribute('D', Attribute.TYPE_INT, 
                                            RatioIndicator, 
                                            kwargs={
                                             'numerator': self.a,
                                             'denominator': self.b
                                            })

        self.view.add_indicator(i)

        value = i.value(self.view, self.record)
        self.assertEqual(value, 5)     
        
        grid = self.view._create_data_grid()[1]
        self.view._update_grid_with_calculated_data(grid)
        
        formated_value = i.format(self.view, grid[0])
        
        self.assertEqual(formated_value , '5.0')
        
        
    def test_rate_indicator(self):
    
        i = Indicator.create_with_attribute('D', Attribute.TYPE_INT, 
                                            RateIndicator, 
                                            kwargs={
                                             'numerator': self.b,
                                             'denominator': self.a
                                            })

        self.view.add_indicator(i)

        value = i.value(self.view, self.record)
        self.assertEqual(value, 20.0)
   
        grid = self.view._create_data_grid()[1]
        self.view._update_grid_with_calculated_data(grid)
        
        formated_value = i.format(self.view, grid[0])
        
        self.assertEqual(formated_value , '20.0 %')
   
        
        
    def test_average_indicator(self):
    
        i = Indicator.create_with_attribute('D', Attribute.TYPE_INT, 
                                            AverageIndicator, 
                                            (self.a, self.b, self.c))

        self.view.add_indicator(i)

        value = i.value(self.view, self.record)
        self.assertEqual(value, 5)      


        grid = self.view._create_data_grid()[1]
        self.view._update_grid_with_calculated_data(grid)
        
        formated_value = i.format(self.view, grid[0])
        
        self.assertEqual(formated_value , '5.0')
        
        
    def test_difference_indicator(self):
    
        i = Indicator.create_with_attribute('D', Attribute.TYPE_INT, 
                                            DifferenceIndicator, 
                                            kwargs={
                                             'first_term': self.b,
                                             'term_to_substract': self.a
                                            })

        self.view.add_indicator(i)

        value = i.value(self.view, self.record)
        self.assertEqual(value, -8) 
        
        grid = self.view._create_data_grid()[1]
        self.view._update_grid_with_calculated_data(grid)
        
        formated_value = i.format(self.view, grid[0])
        
        self.assertEqual(formated_value , '-8')
        
        
    def test_date_indicator(self):
    
        i = Indicator.create_with_attribute('Date', Attribute.TYPE_DATE,
                                            DateIndicator)
        
        self.view.add_indicator(i)
        
        self.record.eav.date = datetime(2000, 1, 2)
        self.record.save()
    
        value = i.value(self.view, self.record)
        self.assertEqual(value, datetime(2000, 1, 2))   
        
        grid = self.view._create_data_grid()[1]
        self.view._update_grid_with_calculated_data(grid)
        
        formated_value = i.format(self.view, grid[0])
        
        self.assertEqual(formated_value , '01/02/2000')
