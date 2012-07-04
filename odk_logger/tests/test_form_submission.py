"""
Testing POSTs to "/submission"
"""
import os
from main.tests.test_base import MainTestCase

class TestFormSubmission(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/tutorial/tutorial.xls"
        )
        self._publish_xls_file(xls_file_path)

    def test_form_post(self):
        """
        xml_submission_file is the field name for the posted xml file.
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/tutorial/instances/tutorial_2012-06-27_11-27-53.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def test_form_post_to_missing_form(self):
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/tutorial/instances/tutorial_invalid_id_string_2012-06-27_11-27-53.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 404)


