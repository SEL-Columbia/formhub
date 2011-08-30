# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from xls2xform.views import home, get_survey
from xform_manager.models import XForm


def index(request):
    kwargs = {
        'extra_links': 'publish_link.html',
        'extra_section': 'published_xforms.html',
        }
    return home(request, **kwargs)


def default_group(user):
    name = user.username
    ct = ContentType.objects.get_by_natural_key(
        app_label='auth', model='permission'
        )
    perm, created = Permission.objects.get_or_create(
        name=name, content_type=ct, codename=name
        )
    group, created = Group.objects.get_or_create(
        name=name
        )
    if perm not in group.permissions.all():
        group.permissions.add(perm)
    return group


def publish(request, survey_id):
    survey = get_survey(request.user, survey_id).export_survey()
    kwargs = {
        'xml': survey.to_xml(),
        'downloadable': True,
        }
    xform, created = XForm.objects.get_or_create(**kwargs)
    xform.groups.add(default_group(request.user))
    return HttpResponseRedirect("/")
