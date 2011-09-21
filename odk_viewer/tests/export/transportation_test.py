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


def publish(username, password, path_to_xls):
    from django.test.client import Client
    client = Client()
    assert client.login(username=username, password=password)
    with open(path_to_xls) as xls_file:
        post_data = {'xls_file': xls_file}
        return client.post('/', post_data)


class TestTransportationSurvey(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="bob")
        self.user.set_password("bob")
        self.user.save()
        self.test_path = os.path.join("odk_viewer", "tests", "export")
        xls_path = os.path.join(self.test_path, "transportation.xls")
        response = publish("bob", "bob", xls_path)
        self.assertEqual(response.status_code, 200)
        odk_path = os.path.join(self.test_path, "odk")
        import_instances_from_phone(odk_path)
        self.assertEqual(XForm.objects.count(), 1)
        self.xform = XForm.objects.all()[0]
        self.set_data_dictionary()

    def test_setup(self):
        self.assertEqual(self.xform.id_string, "transportation_2011_07_25")
        self.assertEqual(self.xform.surveys.count(), 4)

    def test_mongo_entries(self):
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
        for d, mongo_entry in zip(data, self.data_dictionary.get_data_for_excel()):
            for k, v in d.items():
                self.assertEqual(v, mongo_entry["transportation/" + k])

    def test_group_xpaths_should_not_be_added_to_mongo(self):
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

    def test_csv_export(self):
        actual_csv = self._get_csv_()
        f = open(os.path.join(self.test_path, "transportation.csv"), "r")
        expected_csv = csv.reader(f)
        for actual_row, expected_row in zip(actual_csv, expected_csv):
            for actual_cell, expected_cell in zip(actual_row, expected_row):
                self.assertEqual(actual_cell, expected_cell)
        f.close()

    def set_data_dictionary(self):
        # test to make sure the data dictionary returns the expected headers
        self.assertEqual(DataDictionary.objects.count(), 1)
        self.data_dictionary = DataDictionary.objects.all()[0]
        with open(os.path.join(self.test_path, "headers.json")) as f:
            expected_list = json.load(f)
        self.maxDiff = None
        self.assertEqual(self.data_dictionary.get_headers(), expected_list)

        # test to make sure the headers in the actual csv are as expected
        actual_csv = self._get_csv_()
        self.assertEqual(actual_csv.next(), expected_list)

    def test_csv_export2(self):
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
