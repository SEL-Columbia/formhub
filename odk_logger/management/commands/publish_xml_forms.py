#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy
from django.contrib.auth.models import User
from pyxform.xform2json import create_survey_element_from_xml

from odk_logger.models.xform import XForm
from odk_logger.models.instance import get_id_string_from_xml_str


class Command(BaseCommand):
    help = ugettext_lazy("Import a folder of xml forms for ODK.  Arguments-> forder.name  username")

    option_list = BaseCommand.option_list + (
        make_option('-r', '--replace',
            action='store_true',
            dest='replace',
            help=ugettext_lazy("Replace existing form if any")),
        )

    def handle(self, *args, **options):
        path = args[0]

        try:
            username = args[1]
        except IndexError:
            raise CommandError("You must provide the username to publish the forms to.")
        # make sure user exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError("The user '{}' does not exist.".format(username))

        for form in glob.glob( os.path.join(path, "*") ):
            f = open(form)
            xml = f.read()
            id_string = get_id_string_from_xml_str(xml)

            # check if a form with this id_string exists for this user
            form_already_exists = XForm.objects.filter(user=user,
                id_string=id_string).count() > 0

            if form_already_exists:
                if options.has_key('replace') and options['replace']:
                    XForm.objects.filter(user=user, id_string=id_string).delete()
                else:
                    raise CommandError('form "{}" is already defined, and --replace was not specified.'.format(
                        id_string))
            survey = create_survey_element_from_xml(xml)
            form_json = survey.to_json()
            XForm.objects.get_or_create(xml=xml, downloadable=True, user=user, id_string=id_string, json=form_json)
            f.close()
