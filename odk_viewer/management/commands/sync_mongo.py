#!/usr/bin/env python
from optparse import make_option
from django.contrib.auth.models import User

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy
from utils.logger_tools import mongo_sync_status
from odk_logger.models import XForm


class Command(BaseCommand):
    args = '[username] [id_string]'
    help = ugettext_lazy("Check the count of submissions in sqlite vs the "
                         "mongo db per form and optionally run remongo.")
    option_list = BaseCommand.option_list + (
            make_option('-r', '--remongo',
                action='store_true',
                dest='remongo',
                default=False,
                help=ugettext_lazy("Whether to run remongo on the found set.")
            ),
            make_option('-a', '--all',
                action='store_true',
                dest='update_all',
                default=False,
                help=ugettext_lazy(
                    "Update all instances for the selected "
                    "form(s), including existing ones. "
                    "Will delete and re-create mongo records. "
                    "Only makes sense when used with the -r option")
            )
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
                raise CommandError(
                    "Xform %s does not exist for user %s" %\
                    (id_string, user.username))

        remongo = kwargs["remongo"]
        update_all = kwargs["update_all"]

        report_string = mongo_sync_status(remongo, update_all, user, xform)
        self.stdout.write(report_string)
