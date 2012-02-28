from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from main.models import UserProfile
import re


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


def has_permission(xform, owner, request):
    user = request.user
    return xform.shared_data or request.session.get('public_link') or owner == user or\
            user.has_perm('odk_logger.view_xform', xform) or\
            user.has_perm('odk_logger.change_xform', xform)
