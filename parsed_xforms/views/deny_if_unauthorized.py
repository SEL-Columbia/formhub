from functools import update_wrapper, wraps
from django.utils.decorators import available_attrs
from django.shortcuts import render_to_response
from django.template import RequestContext

def access_denied(request):
    context = RequestContext(request)
    return render_to_response(
        "homepage.html",
        context_instance=context
        )

def deny_if_unauthorized(permission="xform.can_view"):
    """
    If the user requesting this page has 'permission' show them the
    view, otherwise show them our access denied page.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.has_perm(permission):
                return view_func(request, *args, **kwargs)
            return access_denied(request)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator
