import base64
import re

from functools import wraps
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404

from guardian.shortcuts import get_perms_for_model, assign_perm
from main.models import UserProfile
from odk_logger.models import XForm
from api.models import Project, Team, OrganizationProfile


class HttpResponseNotAuthorized(HttpResponse):
    status_code = 401

    def __init__(self):
        HttpResponse.__init__(self)
        self['WWW-Authenticate'] =\
            'Basic realm="%s"' % Site.objects.get_current().name


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
    context.profile, created = UserProfile.objects\
        .get_or_create(user=content_user)
    context.location = ""
    if context.profile.city:
        context.location = context.profile.city
    if context.profile.country:
        if context.profile.city:
            context.location += ", "
        context.location += context.profile.country
    context.forms = content_user.xforms.filter(shared__exact=1)
    context.num_forms = context.forms.count()
    context.user_surveys = context.profile.num_of_submissions
    context.home_page = context.profile.home_page
    if context.home_page and re.match("http", context.home_page) is None:
        context.home_page = "http://%s" % context.home_page


def has_permission(xform, owner, request, shared=False):
    user = request.user
    return shared or xform.shared_data or\
        (hasattr(request, 'session') and
         request.session.get('public_link') == xform.uuid) or\
        owner == user or\
        user.has_perm('odk_logger.view_xform', xform) or\
        user.has_perm('odk_logger.change_xform', xform)


def has_edit_permission(xform, owner, request, shared=False):
    user = request.user
    return (shared and xform.shared_data) or owner == user or\
        user.has_perm('odk_logger.change_xform', xform)


def check_and_set_user_and_form(username, id_string, request):
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    owner = User.objects.get(username=username)
    return [xform, owner] if has_permission(xform, owner, request)\
        else [False, False]


def check_and_set_form_by_id(pk, request):
    xform = get_object_or_404(XForm, pk=pk)
    return xform if has_permission(xform, xform.user, request)\
        else False


def get_xform_and_perms(username, id_string, request):
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    is_owner = xform.user == request.user
    can_edit = is_owner or\
        request.user.has_perm('odk_logger.change_xform', xform)
    can_view = can_edit or\
        request.user.has_perm('odk_logger.view_xform', xform)
    return [xform, is_owner, can_edit, can_view]


def helper_auth_helper(request):
    if request.user and request.user.is_authenticated():
        return None
        # source, http://djangosnippets.org/snippets/243/
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2 and auth[0].lower() == "basic":
            uname, passwd = base64.b64decode(auth[1]).split(':')
            user = authenticate(username=uname, password=passwd)
            if user:
                request.user = user
                return None
    response = HttpResponseNotAuthorized()
    return response


def basic_http_auth(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        result = helper_auth_helper(request)
        if result is not None:
            return result
        return func(request, *args, **kwargs)
    return inner


def http_auth_string(username, password):
    credentials = base64.b64encode('%s:%s' % (username, password)).strip()
    auth_string = 'Basic %s' % credentials
    return auth_string


def add_cors_headers(response):
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    response['Access-Control-Allow-Headers'] = ('Accept, Origin,'
                                                ' X-Requested-With,'
                                                ' Authorization')
    response['Content-Type'] = 'application/json'
    return response


def set_api_permissions_for_user(user):
    models = [UserProfile, XForm, Project, Team, OrganizationProfile]
    for model in models:
        for perm in get_perms_for_model(model):
            assign_perm(
                '%s.%s' % (perm.content_type.app_label, perm.codename), user)
