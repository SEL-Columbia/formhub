from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from django.utils.translation import ugettext_lazy, ugettext as _
from common_tags import DELETEDAT, USERFORM_ID, XFORM_ID_STRING, ID
from odk_logger.models.instance import Instance
from odk_viewer.models import ParsedInstance
from odk_viewer.models.parsed_instance import xform_instances, datetime_from_str
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = ugettext_lazy("Update deleted records from mongo to sql instances")

    def handle(self, *args, **kwargs):
        q={"$and": [{"_deleted_at": {"$exists": True}}, {"_deleted_at": {"$ne": None }}]}
        cursor = xform_instances.find(q)
        c = 0
        for record in cursor:
            date_deleted = datetime_from_str(record[DELETEDAT])
            id = record[ID]
            if Instance.set_deleted_at(id, deleted_at=date_deleted):
                c += 1
            print "deleted on ", date_deleted
        print "-------------------------------"
        print "Updated %d records." % c