import traceback

class ExceptionLoggingMiddleware(object):
        def process_exception(self, request, exception):
            import logging
            print traceback.format_exc()
            logging.debug(exception)
            logging.debug(traceback.format_exc())
