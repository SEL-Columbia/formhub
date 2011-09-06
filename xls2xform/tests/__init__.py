#from old_tests import *
#from view_tests import *
#from survey_model_tests import *

from adjuster_test import *
from survey_tests import *
from survey_packager_tests import *


# Why does reverse not work!?!?
from django.test import TestCase
from django.core.urlresolvers import reverse

class ReverseLookupTest(TestCase):
    def setUp(self):
        self.root_name = "fixture1"
        self.survey = Survey.objects.get(root_name=self.root_name)

    def test_first_part_of_packager(self):
        delete_url = \
            reverse('xls2xform.views.delete_survey', kwargs={'survey_root_name': self.root_name})
        edit_url = \
            reverse('xls2xform.views.edit_survey', kwargs={'survey_root_name': self.root_name})