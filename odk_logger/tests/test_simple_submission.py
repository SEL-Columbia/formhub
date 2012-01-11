from django.test import TestCase
import os
import glob
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User
from pyxform import QuestionTypeDictionary, SurveyElementBuilder
from odk_viewer.models import DataDictionary
from odk_logger.models import create_instance, Instance

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
        self.xform = DataDictionary()
        self.xform.user = self.user
        self.xform.json = """
        {"id_string": "yes_or_no", "children": [{"name": "yesno", "label": "Yes or no?", "type": "text"}], "name": "yes_or_no", "title": "yes_or_no", "type": "survey"}
        """.strip()
        qtd = QuestionTypeDictionary("nigeria")
        builder = SurveyElementBuilder(question_type_dictionary=qtd)
        sss = builder.create_survey_element_from_json(self.xform.json)
        self.xform.xml = sss.to_xml()
        self.xform.save()

    def tearDown(self):
        self.xform.delete()
        self.user.delete()

    def test_simple_yes_submission(self):
        self.assertEquals(1, User.objects.count())
        self.assertEquals(1, DataDictionary.objects.count())
        self.assertEquals(0, Instance.objects.count())
        def submit_simple_yes():
            create_instance(self.user.username, TempFileProxy("""
                <?xml version='1.0' ?><yes_or_no id="yes_or_no"><yesno>Yes</yesno></yes_or_no>
                """.strip()), [])
        submit_simple_yes()
        self.assertEquals(1, Instance.objects.count())
        submit_simple_yes()
        self.assertEquals(2, Instance.objects.count())
