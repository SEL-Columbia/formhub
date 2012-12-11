import logging
from datetime import datetime


clog = logging.getLogger('console_logger')

class Enum(object):
    __name__= "Enum"
    def __init__(self, **enums):
        self.enums = enums

    def __getattr__(self, item):
        return self.enums[item]

    def __iter__(self):
        return self.enums.itervalues()

Actions = Enum(
    PROFILE_ACCESSED="profile-accessed",
    PUBLIC_PROFILE_ACCESSED="public-profile-accessed",
    PROFILE_SETTINGS_UPDATED="profile-settings-updated",
    USER_LOGN="user-login",
    USER_LOGOUT="user-logout",
    FORM_ACCESSED="form-accessed",
    FORM_PUBLISH="form-publish",
    FORM_EDIT="form-edit",
    FORM_DELETE="form-delete",
    FORM_ADD_CROWDFORM="form-add-crowdform",
    FORM_REMOVE_CROWDFORM="form-remove-crowdform",
    SUBMISSION_CREATE="submission-create",
    SUBMISSION_EDIT="submission-edit",
    SUBMISSION_DELETE="submission-delete",
    SUBMISSION_API_ACCESSED="submission-api-accessed"
)


class AuditLogHandler(logging.Handler):

    def __init__(self, model=""):
        super(AuditLogHandler, self).__init__()
        self.model_name = model

    def _format(self, record):
        data = {
            'action': record.formhub_action,
            'user': record.request_username,
            'account': record.account_username,
            'audit': {},
            'msg': record.msg,
            # save as python datetime object to have mongo convert to ISO date and allow queries
            'created_on': datetime.utcfromtimestamp(record.created),
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

def audit_log(action, request_user, account_user, message, audit, level=logging.DEBUG):
    """
    Create a log message based on these params

    @param action: Action performed e.g. form-deleted
    @param request_username: User performing the action
    @param account_username: The formhub account the action was performed on
    @param message: The message to be displayed on the log
    @param level: log level
    @param audit: a dict of key/values of other info pertaining to the action e.g. form's id_string, submission uuid
    @return: None
    """
    logger = logging.getLogger("audit_logger")
    extra = {
        'formhub_action': action,
        'request_username': request_user.username if request_user.username
            else str(request_user),
        'account_username': account_user.username if account_user.username
            else str(account_user),
        'formhub_audit': audit
    }
    logger.log(level, message, extra=extra)