# Create your views here.
import os

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.db import IntegrityError

from django.contrib.auth.models import User


@staff_member_required
def submissions(request):
    context = RequestContext(request)

    stats = {}
    stats['submission_count'] = {}
    stats['submission_count']['total_submission_count'] = 0

    users = User.objects.all()
    for user in users:
        stats['submission_count'][user.username] = 0
        for xform in user.xforms.all():
            stats['submission_count'][user.username] += xform.submission_count()
            stats['submission_count']['total_submission_count'] += xform.submission_count()
    context.stats = stats
    return render_to_response("submissions.html", context_instance=context)


@staff_member_required
def stats(request):
    context = RequestContext(request)
    context.template = 'stats.html'
    return render_to_response('base.html', context_instance=context)
