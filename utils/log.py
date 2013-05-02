import logging
from datetime import datetime
from utils.viewer_tools import get_client_ip


class Enum(object):
    __name__= "Enum"
    def __init__(self, **enums):
        self.enums = enums

    def __getattr__(self, item):
        return self.enums[item]

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __iter__(self):
        return self.enums.itervalues()

Actions = Enum(
    PROFILE_ACCESSED="profile-accessed",
    PUBLIC_PROFILE_ACCESSED="public-profile-accessed",
    PROFILE_SETTINGS_UPDATED="profile-settings-updated",
    USER_LOGIN="user-login",
    USER_LOGOUT="user-logout",
    USER_BULK_SUBMISSION="bulk-submissions-made",
    USER_FORMLIST_REQUESTED="formlist-requested",
    FORM_ACCESSED="form-accessed",
    FORM_PUBLISHED="form-published",
    FORM_UPDATED="form-updated",
    FORM_XLS_DOWNLOADED="form-xls-downloaded",
    FORM_XLS_UPDATED="form-xls-updated",
    FORM_DELETED="form-deleted",
    FORM_CLONED="form-cloned",
    FORM_XML_DOWNLOADED="form-xml-downloaded",
    FORM_JSON_DOWNLOADED="form-json-downloaded",
    FORM_PERMISSIONS_UPDATED="form-permissions-updated",
    FORM_ENTER_DATA_REQUESTED="form-enter-data-requested",
    FORM_MAP_VIEWED="form-map-viewed",
    FORM_DATA_VIEWED="form-data-viewed",
    EXPORT_CREATED="export-created",
    EXPORT_DOWNLOADED="export-downloaded",
    EXPORT_DELETED="export-deleted",
    EXPORT_LIST_REQUESTED="export-list-requested",
    SUBMISSION_CREATED="submission-created",
    SUBMISSION_UPDATED="submission-updated",
    SUBMISSION_DELETED="submission-deleted",
    SUBMISSION_ACCESSED="submission-accessed",
    SUBMISSION_EDIT_REQUESTED="submission-edit-requested",
    BAMBOO_LINK_CREATED="bamboo-link-created",
    BAMBOO_LINK_DELETED="bamboo-link-deleted",
    SMS_SUPPORT_ACTIVATED="sms-support-activated",
    SMS_SUPPORT_DEACTIVATED="sms-support-deactivated",
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

    def get_model(self, name):
        names = name.split('.')
        mod = __import__('.'.join(names[:-1]), fromlist=names[-1:])
        return getattr(mod, names[-1])

def audit_log(action, request_user, account_user, message, audit, request, level=logging.DEBUG):
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
        'client_ip': get_client_ip(request),
        'audit': audit
    }
    logger.log(level, message, extra=extra)