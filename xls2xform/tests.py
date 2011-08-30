"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client

from models import *

from django.contrib.auth.models import User


class TestIndexView(TestCase):
    def setUp(self):
        admin = User.objects.create(username="admin")
        admin.set_password("pass")
        admin.save()
        self.c = Client()
        #log in
        self.c.login(username="admin", password="pass")

    def post_new_form(self, id_string, title):
        response = self.c.post("/", {
            'id_string': id_string,
            'title': title,
        }, follow=True)
        if len(response.redirect_chain)==0:
            import pdb
            pdb.set_trace()
        self.assertTrue(len(response.redirect_chain) > 0)
        def spaces_subbed(str):
            import re
            return re.sub(" ", "_", str)
        self.assertEquals(response.redirect_chain[0][0], "http://testserver/edit/%s" % spaces_subbed(id_string))

    def test_new_forms(self):
        inputs = [
            ('id_string1', 'title1'),
            ('id string2', 'title2'), # definitely wont pass
            ('id_string3', 'title with space'),
            #('', 'title'), # definitely wont pass
            #('id_string', ''), # definitely wont pass
            ]
        for input in inputs:
            # Survey.objects.create({
            #     'id_string': input[0],
            #     'title': input[1]
            # })
            self.post_new_form(*input)

class SurveyCreationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.survey = Survey.objects.create(user=self.user, id_string="SimpleId")

    def test_version(self):
        #one version exists by default
        self.assertEqual(self.survey.versions.count(), 1)
        #version is empty
        self.assertEqual(self.survey.latest_version.sections.count(), 0)

    def test_add_section(self):
        sd1 = {u'type':u'text', u'name': u'colour'}
        first_version = self.survey.add_or_update_section(section_dict=sd1, slug="first_section")
        
        #VERSION COUNT INCREMENTED
        self.assertEqual(self.survey.versions.count(), 2)

        #the latest_version should have one section
        self.assertEqual(self.survey.latest_version.sections.count(), 1)

        #  -- add_or_update_section updates when the slug matches
        sd2 = {u'type':u'text', u'name': u'color'}
        second_version = self.survey.add_or_update_section(section_dict=sd2, slug="first_section")

        #  -- the first version should not equal the second version, and other similar tests
        self.assertTrue(first_version != second_version)

        #VERSION COUNT INCREMENTED
        self.assertEqual(self.survey.versions.count(), 3)

        #the latest version should have 1 section still
        self.assertEqual(self.survey.latest_version.sections.count(), 1)

        #we should be able to remove that section
        self.survey.remove_section(slug="first_section")
        self.assertEqual(self.survey.latest_version.sections.count(), 0)
        #removing a section creates a new version
        self.assertEqual(self.survey.versions.count(), 4)

    def tearDown(self):
        self.user.delete()
        self.survey.delete()


class SectionOrderingViaBaseSection(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="TestUser")
        self.survey = Survey.objects.create(user=self.user, id_string="SimpleId")

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
                                          id_string=u"SimpleId",
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
        pyxform_survey_id = s.id_string()

        # The latest version generates a unique id and passes it in
        # the survey object. pyxform should use it.
        self.assertEqual(lv.get_unique_id(), pyxform_survey_id)
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
</h:html>""" % pyxform_survey_id
        self.assertEqual(s.to_xml(), expected_xml)

        sd2 = [
            {
                u'type': u'integer',
                u'name': u'weight'
                }
            ]
        lv2 = self.survey.add_or_update_section(section_dict=sd2, slug="second_section")
        second_section = lv2.sections_by_slug()['second_section']
        lv2 = self.survey.activate_section(second_section)
        pyxform_survey_id = lv2.get_unique_id()

        s = self.survey.export_survey()
        self.assertEqual("""<h:html xmlns="http://www.w3.org/2002/surveys" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><h:head><h:title>SimpleId</h:title><model><instance><SimpleId id="%s"><color/><weight/></SimpleId></instance><bind nodeset="/SimpleId/color" required="true()" type="string"/><bind nodeset="/SimpleId/weight" required="true()" type="int"/></model></h:head><h:body><input ref="/SimpleId/color"><label ref="jr:itext('/SimpleId/color:label')"/></input><input ref="/SimpleId/weight"><label ref="jr:itext('/SimpleId/weight:label')"/></input></h:body></h:html>"""  % pyxform_survey_id, s.to_xml())
    
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
            u'id_string': u'Test_canSpecifyIDstring'
            }
        s = pyxform.create_survey(**survey_package)
        self.assertEqual(s.get_name(), "TestAsurvey")
        self.assertEqual(s.id_string(), "Test_canSpecifyIDstring")
        self.assertEqual(len(s._children), 1)
    #    -- what else do we need to test?
