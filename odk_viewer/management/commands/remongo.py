from django.core.management.base import BaseCommand
from django.conf import settings

from odk_viewer.models import ParsedInstance
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = "Insert all existing parsed instances into MongoDB"

    def handle(self, *args, **kwargs):
        for i, pi in enumerate(queryset_iterator(ParsedInstance.objects.all())):
            pi.update_mongo()
            if (i + 1) % 1000 == 0:
                print 'Updated %d records, flushing MongoDB...' % i
                settings._MONGO_CONNECTION.admin.command({'fsync': 1})
