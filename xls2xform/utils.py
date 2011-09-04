import re
from django.template.defaultfilters import slugify as django_slugify

def slugify(str):
    return re.sub("-", "_", django_slugify(str))

def get_survey(user, id_string):
    return Survey.objects.get(id_string=id_string, user=user)
