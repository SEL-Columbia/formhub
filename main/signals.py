from django.contrib.auth.models import User
from django.db.models.signals import post_save
from utils.user_auth import set_api_permissions_for_user


def set_api_permissions(sender, instance=None, created=False, **kwargs):
    if created:
        set_api_permissions_for_user(instance)
post_save.connect(set_api_permissions, sender=User)
