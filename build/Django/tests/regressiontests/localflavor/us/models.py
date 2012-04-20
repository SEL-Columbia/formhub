from django.db import models
from django.contrib.localflavor.us.models import USStateField
from django.contrib.localflavor.us.models import USPostalCodeField

# When creating models you need to remember to add a app_label as
# 'localflavor', so your model can be found

class USPlace(models.Model):
    state = USStateField(blank=True)
    state_req = USStateField()
    state_default = USStateField(default="CA", blank=True)
    postal_code = USPostalCodeField(blank=True)
    name = models.CharField(max_length=20)
    class Meta:
        app_label = 'localflavor'
