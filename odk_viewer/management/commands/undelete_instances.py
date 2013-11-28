from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from django.utils.translation import ugettext_lazy, ugettext as _
from common_tags import DELETEDAT, USERFORM_ID, XFORM_ID_STRING, ID
from odk_logger.models.instance import Instance
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = ugettext_lazy('Remove "is_deleted" flag from sql instances')

    def handle(self, *args, **kwargs):
        cursor = Instance.objects.filter(is_deleted=True)
        c = 0
        for record in cursor:
            record.date_deleted = None
            record.is_deleted = False
            record.save()
            c += 1
        print "Updated %d records." % c
