"""
Testing POSTs to "/submission" using submission-time validation
"""
import os
from main.tests.test_base import MainTestCase


class TestSubmissionTime_validation(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures/submission_time_validation_x_test.xls"
        )
        self._publish_xls_file_and_set_xform(xls_file_path)

    def test_valid_form_post(self):
        """
        xml_submission_file is the field name for the posted xml file.
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures/submission_time_validation_x_valid.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def test_invalid_form_post(self):
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures/submission_time_validation_x_reject.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 406)
