"""
Set up a signal handler to give permission to users with mdgs.gov.ng
email addresses to read the site. This requires the fixtures in
initial_data.json to define the required group and permission.
"""

from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save

def get_ta_group():
    return Group.objects.get(
        name="Technical Assistants"
        )


def add_user_to_groups_based_on_email_address(sender, **kwargs):
    user = kwargs["instance"]
    assert isinstance(user, User)
    technical_assistants = get_ta_group()
    if user.email.endswith('@mdgs.gov.ng') and \
            technical_assistants not in user.groups.all():
        user.groups.add(technical_assistants)

post_save.connect(add_user_to_groups_based_on_email_address, sender=User)
