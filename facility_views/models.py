from django.db import models
from facilities.models import *

class FacilityTable(models.Model):
    name = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)
    
    @property
    def display_dict(self):
        column_variables = [v.display_dict for v in self.variables.all()]
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
    name = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)
    description = models.CharField(max_length=255, null=True)
    clickable = models.BooleanField(default=False)
    variable_id = models.IntegerField(null=True)
    
    facility_table = models.ForeignKey(FacilityTable, related_name="variables")
    
    @property
    def display_dict(self):
        d = {
            'name': self.name,
            'slug': self.slug,
            'clickable': self.clickable
        }
        if not self.description in [None, '']:
            d['description'] = self.description
        return d
