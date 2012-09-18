#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os
import glob
import csv
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy
from odk_logger.models.xform import XForm, DuplicateUUIDError
from optparse import make_option
from utils.model_tools import update_xform_uuid


class Command(BaseCommand):
    help = ugettext_lazy(
        "Use a csv file with username, id_string and new_uuid to set new uuids")
    option_list = BaseCommand.option_list + (
        make_option('-f', '--file',
            help=ugettext_lazy("Path to csv file")),
    )

    def handle(self, *args, **kwargs):
        # all options are required
        if not kwargs.get('file'):
            raise CommandError("You must provide a path to the csv file")
        # try open the file
        try:
            with open(kwargs.get('file'), "r") as f:
                lines = csv.reader(f)
                i = 0
                for line in lines:
                    try:
                        username = line[0]
                        id_string = line[1]
                        uuid = line[2]
                        update_xform_uuid(username, id_string, uuid)
                    except IndexError:
                        print "line %d is in an invalid format" % (i + 1)
                    except XForm.DoesNotExist:
                        print "XForm with username: %s and id string: %s does not exist"\
                        % (username, id_string, uuid)
                    except DuplicateUUIDError:
                        print "An xform with uuid: %s already exists" % uuid
                    else:
                        i += 1
                        print "Updated %d rows" % i
        except IOError:
            raise CommandError("file %s could not be open" % kwargs.get('file'))
            

