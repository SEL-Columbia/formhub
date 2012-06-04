import os
import glob

from django.contrib.auth.models import User
from django.test import TestCase
from pyxform import SurveyElementBuilder

from utils.logger_tools import create_instance
from odk_logger.models import Instance
from odk_viewer.models import DataDictionary


class TempFileProxy(object):
    """
    create_instance will be looking for a file object,
    with "read" and "close" methods.
    """
    def __init__(self, content):
        self.content = content
    def read(self):
        return self.content
    def close(self):
        pass

class TestSimpleSubmission(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", email="sample@example.com")
        self.user.set_password("pass")
        self.xform1 = DataDictionary()
        self.xform1.user = self.user
        self.xform1.json = """
        {"id_string": "yes_or_no", "children": [{"name": "yesno", "label": "Yes or no?", "type": "text"}], "name": "yes_or_no", "title": "yes_or_no", "type": "survey"}
        """.strip()
        self.xform2 = DataDictionary()
        self.xform2.user = self.user
        self.xform2.json = """
        {"id_string": "start_time", "children": [{"name": "start_time", "type": "start"}], "name": "start_time", "title": "start_time", "type": "survey"}
        """.strip()
        def get_xml_for_form(xform):
            builder = SurveyElementBuilder()#question_type_dictionary=qtd)
            sss = builder.create_survey_element_from_json(xform.json)
            xform.xml = sss.to_xml()
            xform._mark_start_time_boolean()
            xform.save()
        get_xml_for_form(self.xform1)
        get_xml_for_form(self.xform2)

    def tearDown(self):
        self.xform1.delete()
        self.user.delete()

    def test_start_time_boolean_properly_set(self):
        self.assertTrue(self.xform1.has_start_time == False)
        self.assertTrue(self.xform2.has_start_time == True)

    def test_simple_yes_submission(self):
        def submit_simple_yes():
            create_instance(self.user.username, TempFileProxy("""
                <?xml version='1.0' ?><yes_or_no id="yes_or_no"><yesno>Yes</yesno></yes_or_no>
                """.strip()), [])
        self.assertEquals(0, self.xform1.surveys.count())
        submit_simple_yes()
        self.assertEquals(1, self.xform1.surveys.count())
        # a simple "yes" submission *SHOULD* increment the survey count
        submit_simple_yes()
        self.assertEquals(2, self.xform1.surveys.count())

    def test_start_time_submissions(self):
        """
        This test checks to make sure that surveys *with start_time available*
        are marked as duplicates when the XML is a direct match.
        """
        def submit_at_hour(hour):
            st_xml = """
            <?xml version='1.0' ?><start_time id="start_time"><start_time>2012-01-11T%d:00:00.000</start_time></start_time>
            """.strip() % hour
            create_instance(self.user.username, TempFileProxy(st_xml), [])
        self.assertEquals(0, self.xform2.surveys.count())
        submit_at_hour(11)
        self.assertEquals(1, self.xform2.surveys.count())
        submit_at_hour(12)
        self.assertEquals(2, self.xform2.surveys.count())
        # an instance from 11 AM already exists in the database, so it *SHOULD NOT* increment the survey count.
        submit_at_hour(11)
        self.assertEquals(2, self.xform2.surveys.count())
