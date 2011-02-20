from django.db import models
from django.contrib.auth.models import User

class Surveyor(User):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return "Surveyor: %s" % self.name