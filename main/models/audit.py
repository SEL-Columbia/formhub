from django.conf import settings


audit = settings.MONGO_DB.auditlog


class AuditLog(object):

    def __init__(self, data):
        self.data = data

    def save(self):
        return audit.save(self.data)
