"""
Testing POSTs to "/submission"
"""
from django.db.models import Sum
import os
from main.tests.test_base import MainTestCase
from odk_logger.models import XForm, Instance
from odk_viewer.models.parsed_instance import GLOBAL_SUBMISSION_STATS
from stats.models import StatsCount

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

    def test_form_post_with_uuid(self):
        """
        tests the way touch forms post
        """
        self.xform = XForm.objects.all().reverse()[0]
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/tutorial/instances/tutorial_2012-06-27_11-27-53.xml"
        )
        self._make_submission(xml_submission_file_path, add_uuid=True,
                touchforms=True)
        self.assertEqual(self.response.status_code, 201)

    def test_duplicate_submissions(self):
        """
        Test submissions for forms with start and end
        """
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/test_forms/survey_names/survey_names.xls"
        )
        self._publish_xls_file(xls_file_path)
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/test_forms/survey_names/instances/"
            "survey_names_2012-08-17_11-24-53.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 202)
        #/fixtures/test_forms/survey_names

    def test_submission_stats_count(self):
        """Test global submission counts, should not reduce on
        submission delete."""
        submission_count = StatsCount.objects.filter(
            key=GLOBAL_SUBMISSION_STATS).aggregate(Sum('value'))
        self.assertIsNone(submission_count['value__sum'])
        self._publish_transportation_form()
        self.xform  = XForm.objects.get(id_string='transportation_2011_07_25')
        self._make_submissions()
        submission_count = StatsCount.objects.filter(
            key=GLOBAL_SUBMISSION_STATS).aggregate(Sum('value'))
        self.assertIsNotNone(submission_count['value__sum'])
        self.assertEqual(submission_count['value__sum'], 4)

        # deleting submissions should not reduce submission counter
        Instance.objects.all().delete()
        self.assertEqual(Instance.objects.count(), 0)
        submission_count = StatsCount.objects.filter(
            key=GLOBAL_SUBMISSION_STATS).aggregate(Sum('value'))
        self.assertEqual(submission_count['value__sum'], 4)

    def test_unicode_submission(self):
        """Test xml submissions that contain unicode characters
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/tutorial/instances/"
            "tutorial_unicode_submission.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def test_submission_w_mismatched_uuid(self):
        """
        test allowing submissions where xml's form uuid doesnt match any form's uuid for a user, as long as id_string can be matched
        """
        # submit instance with uuid that would not match the forms
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_xform_uuid.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def test_fail_submission_if_no_username(self):
        """
        Test that a submission fails if no username is provided and the uuid's dont match
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_xform_uuid.xml"
        )
        # set touchforms to True to force submission to /submission, without username
        self._make_submission(path=xml_submission_file_path, touchforms=True)
        self.assertEqual(self.response.status_code, 404)

    def test_fail_submission_if_bad_id_string(self):
        """
        Test that a submission fails if no username is provided and the uuid's dont match
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_bad_id_string.xml"
        )
        # set touchforms to True to force submission to /submission, without username
        self._make_submission(path=xml_submission_file_path, touchforms=True)
        self.assertEqual(self.response.status_code, 404)