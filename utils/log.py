import logging


clog = logging.getLogger('console_logger')


class AuditLogHandler(logging.Handler):

    def __init__(self, model=""):
        super(AuditLogHandler, self).__init__()
        self.model_name = model

    def _format(self, record):
        data = {
            'audit': {},
            'msg': record.msg,
            'created_on': record.created,
            'levelno': record.levelno,
            'levelname': record.levelname,
            'args': record.args,
            'funcName': record.funcName,
            'msecs': record.msecs,
            'relativeCreated': record.relativeCreated,
            'thread': record.thread,
            'name': record.name,
            'threadName': record.threadName,
            'exc_info': record.exc_info,
            'pathname': record.pathname,
            'exc_text': record.exc_text,
            'lineno': record.lineno,
            'process': record.process,
            'filename': record.filename,
            'module': record.module,
            'processName': record.processName
        }
        if hasattr(record, 'audit') and isinstance(record.audit, dict):
            data['audit']= record.audit
        return data

    def emit(self, record):
        data = self._format(record)
        # save to mongodb audit_log
        try:
            model = self.get_model(self.model_name)
        except:
            pass
        else:
            log_entry = model(data)
            log_entry.save()
        clog.log(record.levelno, record.msg)

    def get_model(self, name):
        names = name.split('.')
        mod = __import__('.'.join(names[:-1]), fromlist=names[-1:])
        return getattr(mod, names[-1])

