import os
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy, ugettext as _
from django.contrib.auth.models import User
from odk_logger.models import XForm
from utils.backup_tools import create_zip_backup

class Command(BaseCommand):
    args = 'username id_string output_file'
    help = ugettext_lazy("Create a zip backup of a form and all its"
                         " submissions")

    def handle(self, *args, **options):
        try:
            username = args[0]
        except IndexError:
            raise CommandError(_("You must provide the username to publish the"
                                 " form to."))
            # make sure user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(_("The user '%s' does not exist.") % username)

        try:
            id_string = args[1]
        except IndexError:
            raise CommandError(_("You must provide the id_string of the form."))
            # make sure user exists
        try:
            xform = XForm.objects.get(user=user, id_string=id_string)
        except XForm.DoesNotExist:
            raise CommandError(_("The id_string '%s' does not exist.") %
                               id_string)

        try:
            output_file = args[2]
        except IndexError:
            raise CommandError(_("You must provide the path to save the"
                                 " restore file to."))
        else:
            output_file = os.path.realpath(output_file)

        create_zip_backup(output_file, user, xform)