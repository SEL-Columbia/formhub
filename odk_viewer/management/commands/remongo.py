from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from django.utils.translation import ugettext_lazy, ugettext as _
from odk_viewer.models import ParsedInstance
from utils.model_tools import queryset_iterator
from common_tags import USERFORM_ID

class Command(BaseCommand):
    help = ugettext_lazy("Insert all existing parsed instances into MongoDB")
    option_list = BaseCommand.option_list + (
        make_option('--batchsize',
            type='int',
            default=100,
            help=ugettext_lazy("Number of records to process per query")),
        make_option('-u', '--username',
            help=ugettext_lazy("Username of the form user")),
        make_option('-i', '--id_string',
            help=ugettext_lazy("id string of the form"))
    )

    def handle(self, *args, **kwargs):
        ids = None
        # check for username AND id_string - if one exists so must the other
        if (kwargs.get('username') and not kwargs.get('id_string')) or (not\
            kwargs.get('username') and kwargs.get('id_string')):
            raise CommandError("username and idstring must either both be specified or neither")
        elif kwargs.get('username') and kwargs.get('id_string'):
            from odk_logger.models import XForm, Instance
            xform = XForm.objects.get(user__username=kwargs.get('username'),
                id_string=kwargs.get('id_string'))
            ids = [i.pk for i in Instance.objects.filter(xform=xform)]
        # num records per run
        batchsize = kwargs['batchsize']
        start = 0;
        end = start + batchsize
        filter_queryset = ParsedInstance.objects.all()
        # instance ids for when we have a username and id_string
        if ids:
            filter_queryset = ParsedInstance.objects.filter(instance__in=ids)
        # total number of records
        record_count = filter_queryset.count()
        i = 0
        while start < record_count:
            print 'Querying record %s to %s' % (start, end-1)
            queryset = filter_queryset.order_by('pk')[start:end]
            for pi in queryset.iterator():
                pi.update_mongo()
                i += 1
                if (i % 1000) == 0:
                    print 'Updated %d records, flushing MongoDB...' % i
                    settings._MONGO_CONNECTION.admin.command({'fsync': 1})
            start = start + batchsize
            end = min(record_count, start + batchsize)
        # add indexes after writing so the writing operation above is not slowed
        settings.MONGO_DB.instances.create_index(USERFORM_ID)
