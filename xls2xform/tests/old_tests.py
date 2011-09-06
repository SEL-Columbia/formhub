"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from xls2xform.models import *
from django.contrib.auth.models import User





class SectionOrderingViaBaseSection(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.survey = Survey.objects.create(user=self.user, root_name="SimpleId")

        sd1 = [{u'type':u'text', u'name':u'color'}]
        self.survey.add_or_update_section(section_dict=sd1, slug="first_section")

        sd2 = [{u'type':u'text', u'name':u'feeling'}]
        self.survey.add_or_update_section(section_dict=sd2, slug="second_section")

    def test_empty_form_has_empty_base_section(self):
        version = self.survey.latest_version
        self.assertEqual([], version.base_section.questions_list)

    def test_new_section_is_not_yet_added(self):
        """
        Adding a section to an survey shouldn't add it to the base section.
        """
        version = self.survey.latest_version
        self.assertEqual([], version.base_section.questions_list)
        self.assertEqual(3, self.survey.versions.count())
        
        # only when the user chooses to place the sections, 
        # they should be added to the base_section.
        self.survey.order_base_sections(["first_section", "second_section"])
        self.assertEqual(4, self.survey.versions.count())
        
        included_slugs = self.survey.latest_version.base_section.questions_list
        expected_dict = [{u'type':u'include', 'name':u'first_section'}, {u'type':u'include', u'name': u'second_section'}]
        self.assertEqual(included_slugs, expected_dict)
    
    def test_activation_of_section(self):
        section_portfolio, included_base_sections = self.survey.latest_version.all_sections()
        #by default, no sections are included
        self.assertEqual(len(included_base_sections), 0)
        version_count = self.survey.versions.count()
        
        #'activating' one section adds it to the base sections.
        self.survey.activate_section(section_portfolio[0])
        included_base_sections2 = self.survey.latest_version.included_base_sections()
        self.assertEqual(len(included_base_sections2), 1)
        self.assertEqual(self.survey.versions.count(), version_count+1)
        
        #'deactivating' will return the list to the original length.
        self.survey.deactivate_section(section_portfolio[0])
        included_base_sections3 = self.survey.latest_version.included_base_sections()
        self.assertEqual(len(included_base_sections3), 0)
        self.assertEqual(self.survey.versions.count(), version_count+2)
    
    def test_sub_sections_are_recognized(self):
        #a bottom-level include (simple case)
        sd3 = [{u'type':u'include', u'name':u'location'}]
        nv = self.survey.add_or_update_section(section_dict=sd3, slug="some_include")
        incl = nv.sections.get(slug="some_include")
        self.assertEqual(incl.sub_sections(), ['location'])
        
        #a section with an include in a repeat (slightly more complex)
        sd4 = [{u'type':u'loop', u'children':[{u'type': u'include', u'name': u'include2'}]}]
        nv = self.survey.add_or_update_section(section_dict=sd4, slug="some_include2")
        incl = nv.sections.get(slug="some_include2")
        self.assertEqual(incl.sub_sections(), ['include2'])
        #todo: deeper levels of include-ability?


class ExportingFormViaPysurvey(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.survey = Survey.objects.create(user=self.user,
                                          root_name=u"SimpleId",
                                          title=u"SimpleId")

    def test_export(self):
        self.assertEqual(self.survey.versions.count(), 1)

        #set section_json
        kwargs = {
            u'section_dict': {
                u'type': u'survey',
                u'name': u'first_section',
                u'children': [
                    {
                        u'type': u'text',
                        u'name': u'color'
                        }
                    ],
                },
            u'slug': u'first_section',
            }
        lv = self.survey.add_or_update_section(**kwargs)
        self.assertEqual(lv, self.survey.latest_version)

        # note: I needed to activate the section to get things working
        new_section = lv.sections_by_slug()[u'first_section']
        lv = self.survey.activate_section(new_section)
        #self.survey.order_sections([u'first_section'])
        s = self.survey.export_survey()
        pyxform_survey_root_name = s.root_name()

        # The latest version generates a unique id and passes it in
        # the survey object. pyxform should use it.
        self.assertEqual(lv.get_unique_id(), pyxform_survey_root_name)
        self.maxDiff = 3000
        expected_xml = """<h:html xmlns="http://www.w3.org/2002/surveys" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>SimpleId</h:title>
    <model>
      <instance>
        <SimpleId id="%s">
          <color/>
        </SimpleId>
      </instance>
      <bind nodeset="/SimpleId/color" required="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/SimpleId/color">
      <label ref="jr:itext('/SimpleId/color:label')"/>
    </input>
  </h:body>
</h:html>""" % pyxform_survey_root_name
        self.assertEqual(s.to_xml(), expected_xml)

        sd2 = [{ u'type': u'integer',
                    u'name': u'weight' }]
        lv2 = self.survey.add_or_update_section(section_dict=sd2, slug="second_section")
        second_section = lv2.sections_by_slug()['second_section']
        lv2 = self.survey.activate_section(second_section)
        pyxform_survey_root_name = lv2.get_unique_id()

        s = self.survey.export_survey()
        self.assertEqual("""<h:html xmlns="http://www.w3.org/2002/surveys" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><h:head><h:title>SimpleId</h:title><model><instance><SimpleId id="%s"><color/><weight/></SimpleId></instance><bind nodeset="/SimpleId/color" required="true()" type="string"/><bind nodeset="/SimpleId/weight" required="true()" type="int"/></model></h:head><h:body><input ref="/SimpleId/color"><label ref="jr:itext('/SimpleId/color:label')"/></input><input ref="/SimpleId/weight"><label ref="jr:itext('/SimpleId/weight:label')"/></input></h:body></h:html>"""  % pyxform_survey_root_name, s.to_xml())
    
    def tearDown(self):
        self.user.delete()
        self.survey.delete()

import pyxform

class PassValuesToPysurvey(TestCase):
    def test_package_values_create_survey(self):
        survey_package = {
            u'title': u'TestAsurvey',
            u'name_of_main_section': u"TestAsurvey",
            u'sections': {
                u"TestAsurvey": {
                    u'type': u'survey',
                    u'name': u"TestAsurvey",
                    u'children': [
                        {
                            u'type': u'text',
                            u'name': u'name'
                            }
                        ]
                    }
                },
            u'root_name': u'Test_canSpecifyIDstring'
            }
        s = pyxform.create_survey(**survey_package)
        self.assertEqual(s.get_name(), "TestAsurvey")
        self.assertEqual(s.root_name(), "Test_canSpecifyIDstring")
        self.assertEqual(len(s._children), 1)
    #    -- what else do we need to test?
