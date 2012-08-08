from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option
from odk_viewer.models import ParsedInstance
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = "Insert all existing parsed instances into MongoDB"
    option_list = BaseCommand.option_list + (
            make_option('--batchsize',
                default=1000,
                help='Number of records to process per query'),
        )

    def handle(self, *args, **options):
        # num records per run
        records_per_run = options.get("batchsize")
        start = 0;
        end = start + records_per_run
        # total number of records
        record_count = ParsedInstance.objects.count()
        i = 0
        while start < record_count:
            print "Querying record %s to %s" % (start, end)
            for pi in queryset_iterator(ParsedInstance.objects.all()[start:end]):
                pi.update_mongo()
                if (i + 1) % 1000 == 0:
                    print 'Updated %d records, flushing MongoDB...' % i
                    settings._MONGO_CONNECTION.admin.command({'fsync': 1})
            start = start + records_per_run
            end = start + records_per_run
