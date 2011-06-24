from django.db import models
from facilities.models import *

class FacilityTable(models.Model):
    name = models.CharField(max_length=25)
    slug = models.CharField(max_length=25)
    
    def display_dict(self):
        column_variables = []
        for v in self.variables.all():
            column_variables.append({
                'slug': v.slug,
                'name': v.name
            })
        return {
            'name': self.name,
            'slug': self.slug,
            'columns': column_variables
        }
    
    def add_variable(self, variable_data):
        variable_data['facility_table'] = self
        TableColumn.objects.get_or_create(**variable_data)

class TableColumn(models.Model):
    #there's a lot of overlap with facilities.Variable, but there's view-specific stuff
    #that needs a home.
    name = models.CharField(max_length=25)
    slug = models.CharField(max_length=25)
    description = models.CharField(max_length=50, null=True)
    
    variable_id = models.IntegerField(null=True)
    
    facility_table = models.ForeignKey(FacilityTable, related_name="variables")
