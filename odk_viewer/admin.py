from django.contrib import admin
from .models.data_dictionary import DataDictionary
from models.parsed_instance import ParsedInstance

admin.site.register(DataDictionary)
admin.site.register(ParsedInstance)
