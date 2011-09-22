"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from odk_logger import views


class TestFormSubmission(TestCase):

    def test_form_post(self):
        """
        xml_submission_file is the field name for the posted xml file.
        """
        post_data = {
            "xml_submission_file" : (
                "filename.xml",
                #this xml text is not the right way to post a file, so should be replaced.
                "<?xml version='1.0' ?><Example id='Simple Photo Survey'><Location><Picture>1286990143958.jpg</Picture></Location></Example>",
            )
        }
        response = self.client.post("/submission", post_data)
#        self.assertEqual(response.status_code, 200)


