from django.contrib import admin
from . import models

admin.site.register(models.Form)
admin.site.register(models.Submission)
admin.site.register(models.SubmissionImage)
