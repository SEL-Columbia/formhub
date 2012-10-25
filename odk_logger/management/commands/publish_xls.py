import os
from optparse import make_option
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy, ugettext as _
from django.contrib.auth.models import User
from pyxform.builder import create_survey_from_xls
from odk_logger.models.xform import XForm
from utils.logger_tools import publish_xls_form
from utils.viewer_tools import django_file

class Command(BaseCommand):
    args = 'xls_file username'
    help = ugettext_lazy("Publish an XLS file with the option of replacing an"
                        "existing one")

    option_list = BaseCommand.option_list + (
        make_option('-r', '--replace',
            action='store_true',
            dest='replace',
            help=ugettext_lazy("Replace existing form if any")),
        )

    def handle(self, *args, **options):
        try:
            xls_filepath = args[0]
        except IndexError:
            raise CommandError(_("You must provide the path to the xls file."))
        # make sure path exists
        if not os.path.exists(xls_filepath):
            raise CommandError(
                _("The xls file '%s' does not exist.") %
                xls_filepath)

        try:
            username = args[1]
        except IndexError:
            raise CommandError(_("You must provide the username to publish the form to."))
        # make sure user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(_("The user '%s' does not exist.") % username)

        # wasteful but we need to get the id_string beforehand
        survey = create_survey_from_xls(xls_filepath)

        # check if a form with this id_string exists for this user
        form_already_exists = XForm.objects.filter(user=user,
            id_string=survey.id_string).count() > 0

        # id_string of form to replace, if any
        id_string = None
        if form_already_exists:
            if options.has_key('replace') and options['replace']:
                id_string = survey.id_string
                self.stdout.write(_("Form already exist, replacing ..\n"))
            else:
                raise CommandError(_("The form with id_string '%s' already exists, use the -r option to replace it.") % survey.id_string)
        else:
            self.stdout.write(_("Form does NOT exist, publishing ..\n"))

        # publish
        xls_file = django_file(xls_filepath, 'xls_file', 'application/vnd.ms-excel')
        dd = publish_xls_form(xls_file, user, id_string)
        self.stdout.write(_("Done..\n"))