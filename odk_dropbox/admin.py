from django.contrib import admin
from django.forms import ModelForm
from . import models

class XFormInput(ModelForm):
    class Meta:
        model = models.Form
        exclude = ("id_string",)

def make_active(modeladmin, request, queryset):
    queryset.update(active=True)
make_active.short_description = "Mark selected XForms as active"

def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)
make_inactive.short_description = "Mark selected XForms as inactive"

class FormAdmin(admin.ModelAdmin):
    form = XFormInput
    list_display = ("id_string", "instances_count", "active")
    actions = [make_active, make_inactive]

    # http://stackoverflow.com/questions/1618728/disable-link-to-edit-object-in-djangos-admin-display-list-only
    def __init__(self, *args, **kwargs):
        admin.ModelAdmin.__init__(self, *args, **kwargs)
        self.list_display_links = (None, )

admin.site.register(models.Form, FormAdmin)
