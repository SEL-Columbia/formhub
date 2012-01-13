from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import models
from country_field import COUNTRIES
from gravatar import get_gravatar_img_link

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

    def gravatar(self):
        return get_gravatar_img_link(self.user)

