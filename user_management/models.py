"""
The code below creates the permission and group objects we will use to
manage security. We also set up a signal handler to give permission to
all TAs to read data on the site.
"""

# Create the permissions we will need.
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# The following is a slight compromise. The content_type we use for
# defining these permissions doesn't really matter.
ct = ContentType.objects.get(model='ContentType')

read, created = Permission.objects.get_or_create(
    name='read', content_type=ct, codename='read'
    )

# Create a group for the technical assistants, and give the group read
# access.
from django.contrib.auth.models import Group

technical_assistants, created = Group.objects.get_or_create(
    name="Technical Assistants"
    )
if read not in technical_assistants.permissions.all():
    technical_assistants.permissions.add(read)

# Set up a signal handler to add users to the technical assistants
# group.
from django.db.models.signals import post_save
from django.contrib.auth.models import User


def add_user_to_groups_based_on_email_address(sender, **kwargs):
    user = kwargs["instance"]
    assert isinstance(user, User)
    if user.email.endswith('@mdgs.gov.ng') and \
            technical_assistants not in user.groups.all():
        user.groups.add(technical_assistants)


post_save.connect(add_user_to_groups_based_on_email_address, sender=User)
