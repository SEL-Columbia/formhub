from django.db import models
from facilities.models import *

class FacilityTable(models.Model):
    name = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)
    
    @property
    def display_dict(self):
        variables = list(self.variables.all())
        column_variables = [v.display_dict for v in variables]
        return {
            'name': self.name,
            'slug': self.slug,
            'columns': column_variables,
            'subgroups': [{'name': s.name,
                'slug': s.slug} for s in self.subgroups.all()]
        }
    
    def add_column(self, data):
        ColumnCategory.objects.get_or_create(table=self, slug=data['slug'], name=data['name'])
    
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
    click_action = models.CharField(max_length=64, null=True)
    subgroups = models.CharField(max_length=512, null=True)
    variable_id = models.IntegerField(null=True)
    facility_table = models.ForeignKey(FacilityTable, related_name="variables")
    #display specific details
    display_style = models.CharField(max_length=64, null=True)
    #calc specific info
    calc_action = models.CharField(max_length=256, null=True)
    calc_columns = models.CharField(max_length=512, null=True)
    display_order = models.IntegerField()
    
    @property
    def display_dict(self):
        subgroups = []
        if not self.subgroups == "":
            subgroups = self.subgroups.split(" ")
        d = {
            'name': self.name,
            'slug': self.slug,
            'subgroups': subgroups,
            'clickable': self.clickable,
            'click_action': self.click_action,
            'display_order': self.display_order
        }
        if not self.display_style in [None, '']:
            d['display_style'] = self.display_style
        
        if not self.calc_action in [None, '']:
            d['calc_action'] = self.calc_action
            d['calc_columns'] = self.calc_columns
        
        if not self.description in [None, '']:
            d['description'] = self.description
        return d

class ColumnCategory(models.Model):
    name = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)
    table = models.ForeignKey(FacilityTable, related_name='subgroups')
