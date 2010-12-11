from django.contrib import admin
from . import models
from odk_dropbox.models import Submission

admin.site.register(models.Phone)
admin.site.register(models.GPS)
admin.site.register(models.SurveyType)
admin.site.register(models.Surveyor)

def reparse_all(modeladmin, request, queryset):
    models.ParsedSubmission.objects.all().delete()
    for s in Submission.objects.all():
        models.parse(s)
reparse_all.short_description = "Delete and recreate all parsed submissions."

class ParsedSubmissionAdmin(admin.ModelAdmin):
    actions = [reparse_all]

admin.site.register(models.ParsedSubmission, ParsedSubmissionAdmin)
