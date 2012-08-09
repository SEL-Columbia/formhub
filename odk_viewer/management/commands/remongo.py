from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option
from odk_viewer.models import ParsedInstance
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = "Insert all existing parsed instances into MongoDB"
    option_list = BaseCommand.option_list + (
            make_option('--batchsize',
                type='int',
                default=100,
                help='Number of records to process per query'),
        )

    def handle(self, *args, **kwargs):
        print "kwargs: %s" % kwargs
        # num records per run
        batchsize = kwargs['batchsize']
        start = 0;
        end = start + batchsize
        # total number of records
        record_count = ParsedInstance.objects.count()
        i = 0
        while start < record_count:
            print "Querying record %s to %s" % (start, end-1)
            queryset = ParsedInstance.objects.order_by('pk')[start:end]
            for pi in queryset.iterator():
                pi.update_mongo()
                i += 1
                if (i % 1000) == 0:
                    print 'Updated %d records, flushing MongoDB...' % i
                    #settings._MONGO_CONNECTION.admin.command({'fsync': 1})
            start = start + batchsize
            end = start + batchsize
        settings._MONGO_CONNECTION.admin.command({'fsync': 1})
