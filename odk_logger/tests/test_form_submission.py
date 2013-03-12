"""
Testing POSTs to "/submission"
"""
from django.db.models import Sum
import os
import re
from main.tests.test_base import MainTestCase
from odk_logger.models import XForm, Instance
from odk_logger.models.instance import InstanceHistory
from odk_viewer.models.parsed_instance import GLOBAL_SUBMISSION_STATS,\
    ParsedInstance
from stats.models import StatsCount
from odk_logger.xform_instance_parser import clean_and_parse_xml
from common_tags import GEOLOCATION


class TestFormSubmission(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        xls_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../fixtures/tutorial/tutorial.xls"
        )
        self._publish_xls_file_and_set_xform(xls_file_path)

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
            "../fixtures/tutorial/instances/"
            "tutorial_invalid_id_string_2012-06-27_11-27-53.xml"
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
        self._make_submission(
            xml_submission_file_path, add_uuid=True, touchforms=True)
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
        self.xform = XForm.objects.get(id_string='transportation_2011_07_25')
        self._make_submissions()
        submission_count = StatsCount.objects.filter(
            key=GLOBAL_SUBMISSION_STATS).aggregate(Sum('value'))
        self.assertIsNotNone(submission_count['value__sum'])
        stat_submission_count = submission_count['value__sum']

        # deleting submissions should not reduce submission counter
        Instance.objects.all().delete()
        self.assertEqual(Instance.objects.count(), 0)
        submission_count = StatsCount.objects.filter(
            key=GLOBAL_SUBMISSION_STATS).aggregate(Sum('value'))
        self.assertEqual(
            submission_count['value__sum'], stat_submission_count)

    def test_unicode_submission(self):
        """Test xml submissions that contain unicode characters
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_unicode_submission.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)

    def test_duplicate_submission_with_same_instanceID(self):
        """Test duplicate xml submissions
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_uuid.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 202)

    def test_duplicate_submission_with_different_content(self):
        """Test xml submissions with same instancID but different content
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_uuid.xml"
        )
        duplicate_xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_uuid_same_instanceID.xml"
        )
        pre_count = Instance.objects.count()
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)
        self.assertEqual(Instance.objects.count(), pre_count + 1)
        inst = Instance.objects.all().reverse()[0]
        self._make_submission(duplicate_xml_submission_file_path)
        self.assertEqual(self.response.status_code, 202)
        self.assertEqual(Instance.objects.count(), pre_count + 1)
        # this is exactly the same instance
        anothe_inst = Instance.objects.all().reverse()[0]
        # no change in xml content
        self.assertEqual(inst.xml, anothe_inst.xml)

    def test_edited_submission(self):
        """
        Test submissions that have been edited
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_uuid.xml"
        )
        num_instances_history = InstanceHistory.objects.count()
        num_instances = Instance.objects.count()
        query_args = {
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'query': '{}',
            'fields': '[]',
            'sort': '[]',
            'count': True
        }
        cursor = ParsedInstance.query_mongo(**query_args)
        num_mongo_instances = cursor[0]['count']
        # make first submission
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)
        self.assertEqual(Instance.objects.count(), num_instances + 1)
        # no new record in instances history
        self.assertEqual(
            InstanceHistory.objects.count(), num_instances_history)
        # check count of mongo instances after first submission
        cursor = ParsedInstance.query_mongo(**query_args)
        self.assertEqual(cursor[0]['count'], num_mongo_instances + 1)
        # edited submission
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_uuid_edited.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)
        # we must have the same number of instances
        self.assertEqual(Instance.objects.count(), num_instances + 1)
        # should be a new record in instances history
        self.assertEqual(
            InstanceHistory.objects.count(), num_instances_history + 1)
        cursor = ParsedInstance.query_mongo(**query_args)
        self.assertEqual(cursor[0]['count'], num_mongo_instances + 1)
        # make sure we edited the mongo db record and NOT added a new row
        query_args['count'] = False
        cursor = ParsedInstance.query_mongo(**query_args)
        record = cursor[0]
        with open(xml_submission_file_path, "r") as f:
            xml_str = f.read()
        xml_str = clean_and_parse_xml(xml_str).toxml()
        edited_name = re.match(ur"^.+?<name>(.+?)</name>", xml_str).groups()[0]
        self.assertEqual(record['name'], edited_name)

    def test_submission_w_mismatched_uuid(self):
        """
        test allowing submissions where xml's form uuid doesnt match
        any form's uuid for a user, as long as id_string can be matched
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
        Test that a submission fails if no username is provided
        and the uuid's don't match
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_xform_uuid.xml"
        )
        # set touchforms to True to force submission to /submission,
        # without username
        self._make_submission(path=xml_submission_file_path, touchforms=True)
        self.assertEqual(self.response.status_code, 404)

    def test_fail_submission_if_bad_id_string(self):
        """
        Test that a submission fails if no username is provided
        and the uuid's don't match
        """
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_bad_id_string.xml"
        )
        # set touchforms to True to force submission to /submission,
        # without username
        self._make_submission(path=xml_submission_file_path, touchforms=True)
        self.assertEqual(self.response.status_code, 404)

    def test_edit_updated_geopoint_cache(self):
        query_args = {
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'query': '{}',
            'fields': '[]',
            'sort': '[]',
            'count': True
        }
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_uuid.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)
        # query mongo for the _geopoint field
        query_args['count'] = False
        records = ParsedInstance.query_mongo(**query_args)
        self.assertEqual(len(records), 1)
        # submit the edited instance
        xml_submission_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "tutorial", "instances",
            "tutorial_2012-06-27_11-27-53_w_uuid_edited.xml"
        )
        self._make_submission(xml_submission_file_path)
        self.assertEqual(self.response.status_code, 201)
        records = ParsedInstance.query_mongo(**query_args)
        self.assertEqual(len(records), 1)
        cached_geopoint = records[0][GEOLOCATION]
        # the cached geopoint should equal the gps field
        gps = records[0]['gps'].split(" ")
        self.assertEqual(float(gps[0]), float(cached_geopoint[0]))
        self.assertEqual(float(gps[1]), float(cached_geopoint[1]))
