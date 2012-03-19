from django.contrib.auth.models import User
from django.db import models
from utils.country_field import COUNTRIES
from utils.gravatar import get_gravatar_img_link, gravatar_exists
from django.db.models.signals import post_save

class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User, related_name='profile')

    # Other fields here
    name = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, choices=COUNTRIES, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    home_page = models.CharField(max_length=255, blank=True)
    twitter = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    require_auth = models.BooleanField(default=False,
            verbose_name="Require Phone Authentication")

    @property
    def gravatar(self):
        return get_gravatar_img_link(self.user)

    @property
    def gravatar_exists(self):
        return gravatar_exists(self.user)

    class Meta:
        app_label = 'main'

from utils.stathat_api import stathat_count
def stathat_user_signups(sender, instance, created, **kwargs):
    if created:
       stathat_count('formhub-signups')
post_save.connect(stathat_user_signups, sender=UserProfile)
