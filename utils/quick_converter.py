# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django import forms
from odk_viewer.models import DataDictionary

class QuickConverter(forms.Form):
    xls_file = forms.FileField(upload_to="XLS", label="XLS File")

    def publish(self, user):
        if self.is_valid():
            return DataDictionary.objects.create(
                user=user,
                xls=self.cleaned_data['xls_file']
                )

