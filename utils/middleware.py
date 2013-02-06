import traceback

from django.http import HttpResponseNotAllowed
from django.template import RequestContext
from django.template import loader
from django.middleware.locale import LocaleMiddleware
from django.utils.translation.trans_real import parse_accept_lang_header


class ExceptionLoggingMiddleware(object):

    def process_exception(self, request, exception):
        print(traceback.format_exc())


class HTTPResponseNotAllowedMiddleware(object):

    def process_response(self, request, response):
	if isinstance(response, HttpResponseNotAllowed):
	    context = RequestContext(request)
	    response.content = loader.render_to_string("405.html", context_instance=context)
	return response


class LocaleMiddlewareWithTweaks(LocaleMiddleware):
    """
    Overrides LocaleMiddleware from django with:
        Khmer `km` language code in Accept-Language is rewritten to km-kh
    """

    def process_request(self, request):
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        try:
            codes = [code for code, r in parse_accept_lang_header(accept)]
            if 'km' in codes and not 'km-kh' in codes:
                request.META['HTTP_ACCEPT_LANGUAGE'] = accept.replace('km',
                                                                      'km-kh')
        except:
            # this might fail if i18n is disabled.
            pass

        super(LocaleMiddlewareWithTweaks, self).process_request(request)
