from django.contrib import admin
from . import models
from odk_dropbox.models import Submission

admin.site.register(models.Phone)
admin.site.register(models.GPS)
admin.site.register(models.SurveyType)
admin.site.register(models.Location)
admin.site.register(models.Surveyor)

def reparse_all(modeladmin, request, queryset):
    models.ParsedInstance.objects.all().delete()
    for s in Instance.objects.all():
        models.parse(s)
reparse_all.short_description = "Delete and recreate all parsed instances."

class ParsedInstanceAdmin(admin.ModelAdmin):
    actions = [reparse_all]

admin.site.register(models.ParsedInstance, ParsedInstanceAdmin)
