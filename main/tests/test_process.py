from test_base import MainTestCase
from odk_viewer.models import DataDictionary
from odk_logger.models import XForm, Instance
import os
from odk_viewer.views import xls_export, csv_export
from django.core.urlresolvers import reverse
import csv
import json
import urllib2

def internet_on():
    try:
        response=urllib2.urlopen('http://74.125.113.99',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

class TestSite(MainTestCase):

    def test_process(self, username=None, password=None):
        if username is not None:
            self._create_user_and_login(username, password)
        self._publish_xls_file()
        self._check_formList()
        self._download_xform()
        self._make_submissions()
        self._check_csv_export()
        self._check_delete()

    def test_url_upload(self):
        if internet_on():
            self._create_user_and_login()
            xls_url = 'http://formhub.org/pld/forms/transportation_2011_07_25/form.xls'
            pre_count = XForm.objects.count()
            response = self.client.post('/%s/' % self.user.username, {'xls_url': xls_url})
            # make sure publishing the survey worked
            self.assertEqual(response.status_code, 200)
            self.assertEqual(XForm.objects.count(), pre_count+1)

    def test_url_upload_non_dot_xls_path(self):
        if internet_on():
            self._create_user_and_login()
            xls_url = 'https://docs.google.com/spreadsheet/pub?hl=en_US&hl=en_US&key=0AgpC5gsTSm_4dFZQdzZZVGxlcEQ3aktBbFlyRXE3cFE&output=xls'
            pre_count = XForm.objects.count()
            response = self.client.post('/%s/' % self.user.username, {'xls_url': xls_url})
            # make sure publishing the survey worked
            self.assertEqual(response.status_code, 200)
            self.assertEqual(XForm.objects.count(), pre_count+1)

    def _publish_xls_file(self):
        xls_path = os.path.join(self.this_directory, "fixtures", "transportation", "transportation.xls")
        pre_count = XForm.objects.count()
        self.response = MainTestCase._publish_xls_file(self, xls_path)

        # make sure publishing the survey worked
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(XForm.objects.count(), pre_count+1)
        self.xform = list(XForm.objects.all())[-1]
        self.assertEqual(self.xform.id_string, "transportation_2011_07_25")

    def _check_formList(self):
        url = '/%s/formList' % self.user.username
        response = self.anon.get(url)
        self.download_url = 'http://testserver/%s/forms/transportation_2011_07_25/form.xml' % self.user.username
        expected_content = """<forms>
  
  <form url="%s">transportation</form>
  
</forms>
""" % self.download_url
        self.assertEqual(response.content, expected_content)

    def _download_xform(self):
        response = self.anon.get(self.download_url)
        xml_path = os.path.join(self.this_directory, "fixtures", "transportation", "transportation.xml")
        with open(xml_path) as xml_file:
            expected_content = xml_file.read()
        self.assertEqual(expected_content, response.content)

    def _make_submissions(self):
        surveys = ['transport_2011-07-25_19-05-49',
                   'transport_2011-07-25_19-05-36',
                   'transport_2011-07-25_19-06-01',
                   'transport_2011-07-25_19-06-14',]
        paths = [os.path.join(self.this_directory, 'fixtures', 'transportation', 'instances', s, s + '.xml') for s in surveys]
        pre_count = Instance.objects.count()
        for path in paths:
            self._make_submission(path)
        self.assertEqual(Instance.objects.count(), pre_count + 4)
        self.assertEqual(self.xform.surveys.count(), 4)

    def _check_csv_export(self):
        self._check_data_dictionary()
        self._check_data_for_csv_export()
        self._check_group_xpaths_do_not_appear_in_dicts_for_export()
        self._check_csv_export_first_pass()
        self._check_csv_export_second_pass()

    def _check_data_dictionary(self):
        # test to make sure the data dictionary returns the expected headers
        qs = DataDictionary.objects.filter(user=self.user)
        self.assertEqual(qs.count(), 1)
        self.data_dictionary = DataDictionary.objects.all()[0]
        with open(os.path.join(self.this_directory, "fixtures", "transportation", "headers.json")) as f:
            expected_list = json.load(f)
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
        for d_from_db in self.data_dictionary.get_data_for_excel():
            for k, v in d_from_db.items():
                if k != u'_xform_id_string' and v:
                    new_key = k[len('transport/'):]
                    d_from_db[new_key] = d_from_db[k]
                del d_from_db[k]
            self.assertTrue(d_from_db in data)
            data.remove(d_from_db)
        self.assertEquals(data, [])

    def _check_group_xpaths_do_not_appear_in_dicts_for_export(self):
        # todo: not sure which order the instances are getting put
        # into the database, the hard coded index below should be
        # fixed.
        instance = self.xform.surveys.all()[1]
        expected_dict = {
            "transportation": {
                "transport": {
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
            "transport/available_transportation_types_to_referral_facility": "ambulance bicycle",
            "transport/ambulance/frequency_to_referral_facility": "daily",
            "transport/bicycle/frequency_to_referral_facility": "weekly",
            "_xform_id_string": "transportation_2011_07_25",
            }
        self.assertEqual(instance.get_dict(), expected_dict)

    def _get_csv_(self):
        # todo: get the csv.reader to handle unicode as done here:
        # http://docs.python.org/library/csv.html#examples
        url = reverse(csv_export, kwargs={'username': self.user.username, 'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        actual_csv = response.content
        actual_lines = actual_csv.split("\n")
        return csv.reader(actual_lines)

    def _check_csv_export_first_pass(self):
        actual_csv = self._get_csv_()
        f = open(os.path.join(self.this_directory, "fixtures", "transportation", "transportation.csv"), "r")
        expected_csv = csv.reader(f)
        for actual_row, expected_row in zip(actual_csv, expected_csv):
            for actual_cell, expected_cell in zip(actual_row, expected_row):
                self.assertEqual(actual_cell, expected_cell)
        f.close()

    def _check_csv_export_second_pass(self):
        url = reverse(csv_export, kwargs={'username': self.user.username, 'id_string': self.xform.id_string})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        actual_csv = response.content
        actual_lines = actual_csv.split("\n")
        actual_csv = csv.reader(actual_lines)
        headers = actual_csv.next()
        data = [
            {
                "available_transportation_types_to_referral_facility/none": "True"
                },
            {
                "available_transportation_types_to_referral_facility/ambulance": "True",
                "available_transportation_types_to_referral_facility/bicycle": "True",
                "ambulance/frequency_to_referral_facility": "daily",
                "bicycle/frequency_to_referral_facility": "weekly"
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

        dd = DataDictionary.objects.get(pk=self.xform.pk)
        for row, expected_dict in zip(actual_csv, data):
            d = dict(zip(headers, row))
            for k, v in d.items():
                if v in ["n/a", "False"] or k in dd._additional_headers():
                    del d[k]
            self.assertEqual(d, dict([("transport/" + k, v) for k, v in expected_dict.items()]))

    def _check_delete(self):
        self.assertEquals(self.user.xforms.count(), 1)
        self.user.xforms.all()[0].delete()
        self.assertEquals(self.user.xforms.count(), 0)
