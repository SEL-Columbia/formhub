from django import forms
from django.utils.translation import ugettext_lazy as _

from restservice import SERVICE_CHOICES


class  RestServiceForm(forms.Form):
    service_name = \
        forms.CharField(max_length=50, label=_(u"Service Name"),
                        widget=forms.Select(choices=SERVICE_CHOICES))
    service_url = forms.URLField(verify_exists=False, label=_(u"Service URL"))
