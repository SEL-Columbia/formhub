"""
Testing POSTs to "/submission"
"""
from django.test import TestCase
import os
from django.conf import settings
from xform_manager.models import XForm

class TestXFormCreation(TestCase):

    def test_xform_creation(self):
        f = open(os.path.join(
                settings.PROJECT_ROOT, "xform_manager",
                "fixtures", "test_forms", "registration", "forms",
                "test_registration.xml"
                ))
        xml = f.read()
        f.close()
        xform = XForm.objects.create(
            web_title="blah",
            xml=xml
            )
        self.assertEqual(xform.xml, xml)
        self.assertEqual(xform.id_string, "Registration2010-12-04_09-34-00")
        self.assertEqual(xform.title, "Registration")
        self.assertEqual(xform.file_name(), "Registration2010-12-04_09-34-00.xml")
        self.assertTrue(xform.url().endswith("Registration2010-12-04_09-34-00.xml"))
