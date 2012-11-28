#!/usr/bin/env python
from optparse import make_option
from django.contrib.auth.models import User

import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy
from utils.logger_tools import update_mongo_for_xform
from utils.model_tools import queryset_iterator
from odk_logger.models import XForm, Instance
from django.conf import settings

xform_instances = settings.MONGO_DB.instances

class Command(BaseCommand):
    args = '[username] [id_string]'
    help = ugettext_lazy("Check the count of submissions in sqlite vs the mongo db per form and optionally run remongo.")
    option_list = BaseCommand.option_list + (
        make_option('-r', '--remongo',
            action='store_true',
            dest='remongo',
            default=False,
            help=ugettext_lazy("Whether to run remongo on the found set.")),
        )

    def handle(self, *args, **kwargs):
        user = xform = None
        if len(args) > 0:
            username = args[0]
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError("User %s does not exist" % username)
        if len(args) > 1:
            id_string = args[1]
            try:
                xform = XForm.objects.get(user=user, id_string=id_string)
            except XForm.DoesNotExist:
                raise CommandError("Xform %s does not exist for user %s" % (id_string, user.username))
        qs = XForm.objects.only('id_string').select_related('user')
        if user and not xform:
            qs = qs.filter(user=user)
        elif user and xform:
            qs = qs.filter(user=user, id_string=xform.id_string)
        else:
            qs = qs.all()
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
                    total_to_remongo += (instance_count - mongo_count)
                    # should we remongo
                    if kwargs.has_key('remongo') and kwargs['remongo']:
                        self.stdout.write("Running remongo on %s\n-----------------------------------------------\n" %\
                                          xform.id_string)
                        update_mongo_for_xform(xform)
                done += 1
                self.stdout.write("%f %% done ...\n" % ((float(done)/float(total)) * 100))
            line  = "Total to remongo:          %d\nTotal Forms Found:           %d" % (total_to_remongo, found)
            f.write(line)