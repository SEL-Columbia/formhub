from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import models
from utils.country_field import COUNTRIES
from utils.gravatar import get_gravatar_img_link

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
    gravatar_data = None

    @property
    def gravatar(self):
        if not self.gravatar_data:
            self.set_gravatar_data()
        return self.gravatar_data['gravatar']

    @property
    def gravatar_exists(self):
        if not self.gravatar_data:
            self.set_gravatar_data()
        return self.gravatar_data['exists']

    def set_gravatar_data(self):
        data = get_gravatar_img_link(self.user)
        self.gravatar_data = {
            'gravatar': data[0],
            'exists': data[1]
        }

    class Meta:
        app_label = 'main'

