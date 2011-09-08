# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.shortcuts import render_to_response
from django.template import RequestContext

from xform_manager.models import XForm

from xls2xform.exporter import export_survey
from xls2xform.views import QuickConverter


def index(request):
    if request.method == 'POST':
        form = QuickConverter(request.POST, request.FILES)
        if form.is_valid():
            survey = form.get_survey()
            publish(request.user, survey)
            form = QuickConverter()
    else:
        form = QuickConverter()

    context = RequestContext(request)
    context.form = form
    return render_to_response("dashboard.html", context_instance=context)


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


def publish(user, survey):
    kwargs = {
        'xml': survey.to_xml(),
        'downloadable': True,
        'user': user,
        }
    xform, created = XForm.objects.get_or_create(**kwargs)

    # need to also make a data dictionary
