from django.contrib import admin
from . import models

admin.site.register(models.Form)
admin.site.register(models.Instance)
admin.site.register(models.InstanceImage)
admin.site.register(models.Submission)
