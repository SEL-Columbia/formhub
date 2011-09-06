import re
from django.template.defaultfilters import slugify as django_slugify

def slugify(str):
    return re.sub("-", "_", django_slugify(str))

def get_survey(user, root_name):
    return Survey.objects.get(root_name=root_name, user=user)
