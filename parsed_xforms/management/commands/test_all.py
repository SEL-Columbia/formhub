#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

"""
python manage.py test pyxform locations parsed_xforms nga_districts phone_manager surveyor_manager xform_manager map_xforms submission_qr data_dictionary
"""

from django.core.management.base import BaseCommand
from optparse import make_option
from south.management.commands import patch_for_test_db_setup

import sys

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--failfast', action='store_true', dest='failfast', default=False,
            help='Tells Django to stop running the test suite after first failed test.')
    )
    help = 'A shortcut for testing all the apps in active development.'

    requires_model_validation = False

    def handle(self, *test_labels, **options):
        from django.conf import settings
        from django.test.utils import get_runner
        patch_for_test_db_setup()
        
        test_labels = ('locations', 'parsed_xforms', \
                    'nga_districts', 'phone_manager', 'surveyor_manager', \
                    'xform_manager', 'map_xforms', 'submission_qr',)
        
        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive', True)
        failfast = options.get('failfast', False)
        TestRunner = get_runner(settings)
        
        if hasattr(TestRunner, 'func_name'):
            # Pre 1.2 test runners were just functions,
            # and did not support the 'failfast' option.
            import warnings
            warnings.warn(
                'Function-based test runners are deprecated. Test runners should be classes with a run_tests() method.',
                PendingDeprecationWarning
            )
            failures = TestRunner(test_labels, verbosity=verbosity, interactive=interactive)
        else:
            test_runner = TestRunner(verbosity=verbosity, interactive=interactive, failfast=failfast)
            failures = test_runner.run_tests(test_labels)

        if failures:
            sys.exit(bool(failures))
