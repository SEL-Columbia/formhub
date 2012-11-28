#!/usr/bin/env python

import os
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from utils.model_tools import queryset_iterator
from odk_logger.models import XForm, Instance
from django.conf import settings

xform_instances = settings.MONGO_DB.instances

class Command(BaseCommand):
    help = ugettext_lazy("Check the count of submissions vs the mongo db records for each form.")

    def handle(self, *args, **kwargs):
        #path = args[0]
        qs = XForm.objects.all()
        total = qs.count()
        done = 0
        found = 0
        total_to_remongo = 0
        with open("mongo_vs_instance_counts_report.txt", "w") as f:
            for xform in queryset_iterator(qs, 100):
                # get the count
                user = xform.user
                instance_count = Instance.objects.filter(xform=xform).count()
                userform_id = "%s_%s" % (user.username, xform.id_string)
                mongo_count = xform_instances.find({"_userform_id": userform_id}).count()
                if instance_count != mongo_count:
                    line = "%s @ %s\nInstance count: %d           Mongo count: %d\n--------------------------------------\n" %\
                           (user.username, xform.id_string, instance_count, mongo_count)
                    f.write(line)
                    found += 1
                    total_to_remongo += instance_count
                done += 1
                print "%f %% done ..." % ((float(done)/float(total)) * 100)
            line  = "Total to remongo:          %d\nTotal Forms Found:           %d" % (total_to_remongo, found)
            f.write(line)