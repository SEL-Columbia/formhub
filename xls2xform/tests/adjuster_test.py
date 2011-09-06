from django.test import TestCase
from xls2xform import section_adjuster
from xls2xform.models import SurveySection, Survey
import json

from xls2xform.tests import utils

class SectionAdjusterTest(TestCase):
    def setUp(self):
        self.survey = Survey.objects.get(root_name="fixture1")
        self.ss = [self.survey._sections.get(slug=ss) for ss in 's1 s2 s3'.split(' ')]
        self.middle_section = self.ss[1]
        self.base = self.survey.base_section
    
    def test_temporary_methods(self):
        #_section_slugs returns slugs in alphabetical order
        dbslugs = self.survey._section_slugs
        slugs = 's1 s2 s3 _base'.split(' ')
        slugs.sort()
        self.assertEqual(dbslugs, slugs)
        
        expected = {  "s3": [
                        {"type": "text","name": "text3"}
                      ],
                      "s2": [
                        {"type": "text","name": "text2"}
                      ],
                      "s1": [
                        {"type": "text","name": "text1"}
                      ],
                      "_base": [
                        {"type": "include","name": "s1"},
                        {"type": "include","name": "s2"},
                        {"type": "include","name": "s3"}]}
        expected_tuple = (expected.pop('_base'), expected, )
        self.assertEqual(expected_tuple,
                            self.survey._sections_data_by_slug)

    def test_add_or_update_section(self):
        before_base, before_sections = self.survey._sections_data_by_slug

        s2_update = [{u"type": u"text", u"name": "text999"}]
        self.survey.add_or_update_section(slug="s2", children_json=json.dumps(s2_update))

        after_base, after_sections = self.survey._sections_data_by_slug

        # after_section has one dict that has been updated
        before_sections[u's2'] = s2_update
        self.assertEqual(before_sections, after_sections)

    def test_section_make_adjustment(self):
        self.assertEqual(self.ss[1].slug, self.middle_section.slug)
        self.assertEqual(utils._sn(*self.base._children), u's1 s2 s3'.split(' '))
        self.ss[1].make_adjustment(self.base, 'up')
        newbase = SurveySection.objects.get(slug="_base")
        self.assertEqual(utils._sn(*newbase._children), u's2 s1 s3'.split(' '))

class DictAdjusterTest(TestCase):
    def setUp(self):
        self.base_sections = utils._qd('include:s1', 'include:s2', 'include:s3')

    def test_children(self):
        self.assertEqual(utils._sn(*self.base_sections),
                [u's1', u's2', u's3'])

    def test_adjustment(self):
        new_order = section_adjuster.make_adjustment(self.base_sections, self.base_sections[1], 'up')
        self.assertEqual(utils._sn(*new_order),
                [u's2', u's1', u's3'])
        new_order2 = section_adjuster.make_adjustment(new_order, self.base_sections[1], 'down')
        self.assertEqual(utils._sn(*new_order2),
                [u's1', u's2', u's3'])

    def test_activate_deactivate(self):
        new_order = \
            section_adjuster.make_adjustment(self.base_sections, self.base_sections[1], 'deactivate')
        self.assertEqual(utils._sn(*new_order),
                [u's1', u's3'])

        new_order2 = \
            section_adjuster.make_adjustment(new_order, self.base_sections[1], 'activate')
        self.assertEqual(utils._sn(*new_order2),
                [u's1', u's3', u's2'])
