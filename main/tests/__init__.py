from django.test import TestCase
from django.contrib.auth.models import User
from odk_viewer.models import DataDictionary
from odk_logger.import_tools import import_instances_from_phone
from odk_logger.models import XForm
import os
from odk_viewer.views import csv_export
from django.core.urlresolvers import reverse
import csv
import json
from django.test.client import Client


class TestSite(TestCase):

    def test_process(self):
        self._create_user_and_login()
        self._publish_xls_file()
        self._check_formList()
        self._download_xform()
        self._make_submissions()
        self._check_csv_export()

    def _create_user_and_login(self):
        self.user = User.objects.create(username="bob")
        self.user.set_password("bob")
        self.user.save()
        self.client = Client()
        assert self.client.login(username="bob", password="bob")

    def _publish_xls_file(self):
        self.this_directory = os.path.join("main", "tests")
        xls_path = os.path.join(self.this_directory, "transportation.xls")
        with open(xls_path) as xls_file:
            post_data = {'xls_file': xls_file}
            response = self.client.post('/', post_data)

        # make sure publishing the survey worked
        self.assertEqual(response.status_code, 200)
        self.assertEqual(XForm.objects.count(), 1)
        self.xform = XForm.objects.all()[0]
        self.assertEqual(self.xform.id_string, "transportation_2011_07_25")

    def _check_formList(self):
        pass

    def _download_xform(self):
        pass

    def _make_submissions(self):
        odk_path = os.path.join(self.this_directory, "odk")
        import_instances_from_phone(odk_path)
        self.assertEqual(self.xform.surveys.count(), 4)

    def _check_csv_export(self):
        self._check_data_dictionary()
        self._check_data_for_csv_export()
        self._check_group_xpaths_do_not_appear_in_dicts_for_export()
        self._check_csv_export_first_pass()
        self._check_csv_export_second_pass()

    def _check_data_dictionary(self):
        # test to make sure the data dictionary returns the expected headers
        self.assertEqual(DataDictionary.objects.count(), 1)
        self.data_dictionary = DataDictionary.objects.all()[0]
        with open(os.path.join(self.this_directory, "headers.json")) as f:
            expected_list = json.load(f)
        self.maxDiff = None
        self.assertEqual(self.data_dictionary.get_headers(), expected_list)

        # test to make sure the headers in the actual csv are as expected
        actual_csv = self._get_csv_()
        self.assertEqual(actual_csv.next(), expected_list)

    def _check_data_for_csv_export(self):
        data = [
            {
                "available_transportation_types_to_referral_facility/ambulance": True,
                "available_transportation_types_to_referral_facility/bicycle": True,
                "ambulance/frequency_to_referral_facility": "daily",
                "bicycle/frequency_to_referral_facility": "weekly"
                },
            {
                "available_transportation_types_to_referral_facility/none": True
                },
            {
                "available_transportation_types_to_referral_facility/ambulance": True,
                "ambulance/frequency_to_referral_facility": "weekly",
                },
            {
                "available_transportation_types_to_referral_facility/taxi": True,
                "available_transportation_types_to_referral_facility/other": True,
                "available_transportation_types_to_referral_facility_other": "camel",
                "taxi/frequency_to_referral_facility": "daily",
                "other/frequency_to_referral_facility": "other",
                }
            ]
        for d, d_from_db in zip(data, self.data_dictionary.get_data_for_excel()):
            for k, v in d.items():
                self.assertEqual(v, d_from_db["transportation/" + k])

    def _check_group_xpaths_do_not_appear_in_dicts_for_export(self):
        instance = self.xform.surveys.all()[0]
        expected_dict = {
            "transportation": {
                "transportation": {
                    "bicycle": {
                        "frequency_to_referral_facility": "weekly"
                        },
                    "ambulance": {
                        "frequency_to_referral_facility": "daily"
                        },
                    "available_transportation_types_to_referral_facility": "ambulance bicycle",
                    }
                }
            }
        self.assertEqual(instance.get_dict(flat=False), expected_dict)
        expected_dict = {
            "transportation/available_transportation_types_to_referral_facility": "ambulance bicycle",
            "transportation/ambulance/frequency_to_referral_facility": "daily",
            "transportation/bicycle/frequency_to_referral_facility": "weekly",
            "_xform_id_string": "transportation_2011_07_25",
            }
        self.assertEqual(instance.get_dict(), expected_dict)

    def _get_csv_(self):
        # todo: get the csv.reader to handle unicode as done here:
        # http://docs.python.org/library/csv.html#examples
        url = reverse(csv_export, kwargs={'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        actual_csv = response.content
        actual_lines = actual_csv.split("\n")
        return csv.reader(actual_lines)

    def _check_csv_export_first_pass(self):
        actual_csv = self._get_csv_()
        f = open(os.path.join(self.this_directory, "transportation.csv"), "r")
        expected_csv = csv.reader(f)
        for actual_row, expected_row in zip(actual_csv, expected_csv):
            for actual_cell, expected_cell in zip(actual_row, expected_row):
                self.assertEqual(actual_cell, expected_cell)
        f.close()

    def _check_csv_export_second_pass(self):
        url = reverse(csv_export, kwargs={'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        actual_csv = response.content
        actual_lines = actual_csv.split("\n")
        actual_csv = csv.reader(actual_lines)
        headers = actual_csv.next()
        data = [
            {
                "available_transportation_types_to_referral_facility/ambulance": "True",
                "available_transportation_types_to_referral_facility/bicycle": "True",
                "ambulance/frequency_to_referral_facility": "daily",
                "bicycle/frequency_to_referral_facility": "weekly"
                },
            {
                "available_transportation_types_to_referral_facility/none": "True"
                },
            {
                "available_transportation_types_to_referral_facility/ambulance": "True",
                "ambulance/frequency_to_referral_facility": "weekly",
                },
            {
                "available_transportation_types_to_referral_facility/taxi": "True",
                "available_transportation_types_to_referral_facility/other": "True",
                "available_transportation_types_to_referral_facility_other": "camel",
                "taxi/frequency_to_referral_facility": "daily",
                "other/frequency_to_referral_facility": "other",
                }
            ]

        l = list(self.xform.data_dictionary.all())
        self.assertTrue(len(l) == 1)
        dd = l[0]
        self.maxDiff = None
        for row, expected_dict in zip(actual_csv, data):
            d = dict(zip(headers, row))
            for k, v in d.items():
                if v in ["n/a", "False"] or k in dd._additional_headers():
                    del d[k]
            self.assertEqual(d, dict([("transportation/" + k, v) for k, v in expected_dict.items()]))
