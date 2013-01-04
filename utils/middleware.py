import traceback

from django.http import HttpResponseNotAllowed
from django.template import RequestContext
from django.template import loader
from django.core.urlresolvers import reverse
from django.contrib.auth.views import logout
from utils.log import audit_log, Actions
from django.utils.translation import ugettext as _


class ExceptionLoggingMiddleware(object):

    def process_exception(self, request, exception):
        print(traceback.format_exc())


class HTTPResponseNotAllowedMiddleware(object):

    def process_response(self, request, response):
	if isinstance(response, HttpResponseNotAllowed):
	    context = RequestContext(request)
	    response.content = loader.render_to_string("405.html", context_instance=context)
	return response

class AuditLogLogoutMiddleware(object):
    def process_request(self, request):
        # check if this is the logout url
        logout_url = reverse(logout)
        if logout_url == request.path:
            audit_log(Actions.USER_LOGOUT, request.user, request.user,
                _("Logged out of account."), {}, request)
        return None
