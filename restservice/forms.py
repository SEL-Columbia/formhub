from django import forms
from restservice import SERVICE_CHOICES

class  RestServiceForm(forms.Form):
    service_name = forms.CharField(max_length=50, label=u"Service Name",
        widget=forms.Select(choices=SERVICE_CHOICES))
    service_url = forms.URLField(verify_exists=False, label=u"Service URL")
