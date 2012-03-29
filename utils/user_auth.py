import re

from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from main.models import UserProfile
from odk_logger.models import XForm


def check_and_set_user(request, username):
    if username != request.user.username:
        return HttpResponseRedirect("/%s" % username)
    content_user = None
    try:
        content_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseRedirect("/")
    return content_user


def set_profile_data(context, content_user):
    # create empty profile if none exists
    context.content_user = content_user
    context.profile, created = UserProfile.objects.get_or_create(user=content_user)
    context.location = ""
    if content_user.profile.city:
        context.location = content_user.profile.city
    if content_user.profile.country:
        if content_user.profile.city:
            context.location += ", "
        context.location += content_user.profile.country
    context.forms= content_user.xforms.filter(shared__exact=1).order_by('-date_created')
    context.num_forms= len(context.forms)
    context.home_page = context.profile.home_page
    if context.home_page and re.match("http", context.home_page) == None:
        context.home_page = "http://%s" % context.home_page


def has_permission(xform, owner, request, shared=False):
    user = request.user
    return shared or xform.shared_data or request.session.get('public_link') or\
            owner == user or\
            user.has_perm('odk_logger.view_xform', xform) or\
            user.has_perm('odk_logger.change_xform', xform)


def check_and_set_user_and_form(username, id_string, request):
    xform = get_object_or_404(XForm,
            user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    return [xform, owner] if has_permission(xform, owner, request)\
            else [False, False]


def get_xform_and_perms(username, id_string, request):
    xform = get_object_or_404(XForm,
            user__username=username, id_string=id_string)
    is_owner = username == request.user.username
    can_edit = is_owner or\
            request.user.has_perm('odk_logger.change_xform', xform)
    can_view = can_edit or\
            request.user.has_perm('odk_logger.view_xform', xform)
    return [xform, is_owner, can_edit, can_view]
