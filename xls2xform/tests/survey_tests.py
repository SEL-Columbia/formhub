from django.test import TestCase
from django.contrib.auth.models import User
from xls2xform.models import Survey, SurveySection


class SurveyFixturesLoaded(TestCase):
    """
    initial_data.json has 1 survey with 4 sections:
    
    [BASE SECTION]
       * s1 [text:text1]
       * s2 [text:text2]
       * s3 [text:text3]
    """
    def test_survey_was_loaded(self):
        self.assertTrue(Survey.objects.count() > 0)
        self.assertEquals(Survey.objects.filter(root_name="fixture1").count(), 1)
        self.assertEquals(Survey.objects.get(root_name="fixture1").survey_sections.count(), 4)
        self.assertEquals(Survey.objects.get(root_name="fixture1").base_section.slug, "_base")

class SurveyCreationTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.get(root_name="fixture1")
    
    def test_something(self):
        self.assertEqual(self.survey._sections.count(), 4)