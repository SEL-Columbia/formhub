# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.db.models import Count
from nga_districts.models import LGA
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


def publish(request, id_string):
    survey = get_survey(request.user, id_string).export_survey()
    kwargs = {
        'xml': survey.to_xml(),
        'downloadable': True,
        'groups': [default_group(request.user)],
        }
    xform, created = XForm.objects.get_or_create(**kwargs)


def list_active_lgas(request):
    context = RequestContext(request)
    context.site_title = "NMIS: LGA List"
    context.lgas = LGA.objects.annotate(facility_count=Count('facilities')).filter(facility_count__gt=0)
    return render_to_response("list_active_lgas.html", context_instance=context)

def site_description(request):
    return render_to_response("site_description.html")

def baseline_redirect(request):
    return HttpResponseRedirect("/baseline/")
