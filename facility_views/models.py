from django.db import models
from facilities.models import *

class FacilityTable(models.Model):
    name = models.CharField(max_length=25)
    slug = models.CharField(max_length=25)
    variables = models.ManyToManyField(Variable, related_name="display_tables")
    
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
        
