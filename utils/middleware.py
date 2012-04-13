import traceback

class ExceptionLoggingMiddleware(object):

    def process_exception(self, request, exception):
        print(traceback.format_exc())
