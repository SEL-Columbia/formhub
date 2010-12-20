from django.contrib import admin
from django.forms import ModelForm
from . import models

class XFormInput(ModelForm):
    class Meta:
        model = models.Form
        exclude = ("id_string",)

class FormAdmin(admin.ModelAdmin):
    form = XFormInput
    list_display = ("id_string", "active")

admin.site.register(models.Form, FormAdmin)
