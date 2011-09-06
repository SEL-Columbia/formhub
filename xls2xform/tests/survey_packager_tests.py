import json
from django.test import TestCase
from django.contrib.auth.models import User

from xls2xform.models import Survey, SurveySection
from xls2xform.pyxform_include_packager import gather_includes
from xls2xform.tests import utils

class SurveyExportTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.get(root_name="fixture1")

    def test_first_part_of_packager(self):
        expected_package = {
            "main_section": [
                { "type": "include", "name": "s1" },
                { "type": "include", "name": "s2" },
                { "type": "include", "name": "s3" }
            ],
            "available_sections": {
                "s1": [ { "type": "text", "name": "text1" } ],
                "s3": [ { "type": "text", "name": "text3" } ],
                "s2": [ { "type": "text", "name": "text2" } ]
            }
        }
        output_package = self.survey._survey_package()
        self.assertEqual(output_package['main_section'], expected_package['main_section'])
        self.assertEqual(output_package['sections'], expected_package['available_sections'])

    def test_includes_gathered(self):
        """
        gather_includes should take the base section and a dict of available sections and
        smush them together.
        """
        question_arr = [{ "type": "text", "name": "text1" },
                            { "type": "text", "name": "text2" },
                            { "type": "text", "name": "text3" }]
        question_arr = [{"type": "text", "name": name} for name in 
                                ["text1", "text2", "text3"]]
        output_package = self.survey._survey_package()
        processed = gather_includes(output_package['main_section'],
                            output_package['sections'], [])
        self.assertEqual(processed, question_arr)

class ActivatorTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.get(root_name="fixture1")
        self.section2 = SurveySection.objects.get(slug="s2")

    def test_section_adjuster(self):
        names = utils._names_as_strings(self.survey._base_section)
        self.assertEqual(names, u's1 s2 s3'.split(' '))

    def test_deactivation(self):
        self.assertEqual(self.section2.slug, 's2')
        base = self.survey._base_section
        original_names = utils._names_as_strings(base)
        self.assertEqual(original_names, u's1 s2 s3'.split(' '))
        self.section2.make_adjustment(base, 'deactivate')
        names = utils._names_as_strings(base)
        self.assertEqual(names, u's1 s3'.split(' '))

    def test_add_or_update_section(self):
        s2q1 = self.section2._children[0]
        self.assertEqual(s2q1['name'], 'text2')
        s2q1.update({'name': 'newText2'})
        self.survey.add_or_update_section(slug='s2', children_json=json.dumps(s2q1))
