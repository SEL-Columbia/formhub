#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from django.forms import ModelForm
from . import models

class XFormInput(ModelForm):
    class Meta:
        model = models.XForm
        exclude = ("id_string","title")

def toggle(modeladmin, request, queryset):
    for form in queryset:
        form.active = not form.active
        form.save()
toggle.short_description = "Toggle active status of selected XForms"

class XFormAdmin(admin.ModelAdmin):
    form = XFormInput
    list_display = ("title", "id_string", "description", "submission_count", "active")
    actions = [toggle]

    # http://stackoverflow.com/questions/1618728/disable-link-to-edit-object-in-djangos-admin-display-list-only
    def __init__(self, *args, **kwargs):
        admin.ModelAdmin.__init__(self, *args, **kwargs)
        self.list_display_links = (None, )

admin.site.register(models.XForm, XFormAdmin)
admin.site.register(models.Phone)
admin.site.register(models.Surveyor)
