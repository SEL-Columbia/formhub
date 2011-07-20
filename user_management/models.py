"""
Set up a signal handler to give permission to users with mdgs.gov.ng
email addresses to read the site.
"""
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission, Group
from django.db.models.signals import post_save


def get_ta_group():
    """
    Return a Django Group object for the Technical Assistants. This
    group needs permission to access the site.

    This function is a candidate for caching.
    """
    ct = ContentType.objects.get_by_natural_key(
        app_label='auth', model='permission'
        )
    read, created = Permission.objects.get_or_create(
        name='read', content_type=ct, codename='read'
        )
    technical_assistants, created = Group.objects.get_or_create(
        name="Technical Assistants"
        )
    if read not in technical_assistants.permissions.all():
        technical_assistants.permissions.add(read)
    return technical_assistants


def add_user_to_groups_based_on_email_address(sender, **kwargs):
    user = kwargs["instance"]
    assert isinstance(user, User)
    technical_assistants = get_ta_group()
    if user.email.endswith('@mdgs.gov.ng') and \
            technical_assistants not in user.groups.all():
        user.groups.add(technical_assistants)


post_save.connect(add_user_to_groups_based_on_email_address, sender=User)
