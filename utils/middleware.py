import traceback

from django.http import HttpResponseNotAllowed
from django.template import RequestContext
from django.template import loader


class ExceptionLoggingMiddleware(object):

    def process_exception(self, request, exception):
        print(traceback.format_exc())


class HTTPResponseNotAllowedMiddleware(object):

    def process_response(self, request, response):
	if isinstance(response, HttpResponseNotAllowed):
	    context = RequestContext(request)
	    response.content = loader.render_to_string("405.html", context_instance=context)
	return response
