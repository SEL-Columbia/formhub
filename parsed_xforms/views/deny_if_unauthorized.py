from django.template import RequestContext
from django.shortcuts import render_to_response

def access_denied(request):
    context = RequestContext(request)
    return render_to_response(
        "access_denied.html",
        context_instance=context
        )

from functools import update_wrapper, wraps
from django.utils.decorators import available_attrs
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils.http import urlquote

def deny_if_unauthorized(permission="xform.can_view"):
    """
    If the user requesting this page has 'permission' show them the
    view, if the user is anonymous redirect them to the login page,
    otherwise show them our access denied page.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            # todo: for testing purposes this decorator is turned off
            # this should not be the case, the tests should log in.
            if user.has_perm(permission) or settings.TESTING_MODE:
                return view_func(request, *args, **kwargs)
            elif user.is_anonymous():
                path = urlquote(request.get_full_path())
                pair = (settings.LOGIN_URL, path)
                redirect_url = '%s?next=%s' % pair
                return HttpResponseRedirect(redirect_url)
            else:
                return access_denied(request)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator
