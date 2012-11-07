import glob
import os
from django.test import TestCase
from django.contrib.auth.models import User
from odk_logger.models import XForm, Instance


def open_all_files(path):
    file_paths = glob.glob(os.path.join(path, "*"))
    result = {}
    for file_path in file_paths:
        if file_path.endswith(".jpg"):
            # note the "rb" mode is to open a binary file
            result[file_path] = open(file_path, "rb")
        else:
            result[file_path] = open(file_path)
    return result


def create_post_data(path):
    xml_files = glob.glob(os.path.join(path, "*.xml"))
    if len(xml_files) != 1:
        raise Exception("There should be a single XML file in this directory.")
    xml_file = open(xml_files[0])
    post_data = {"xml_submission_file": xml_file}

    for jpg in glob.glob(os.path.join(path, "*.jpg")):
        # note the "rb" mode is to open a binary file
        image_file = open(jpg, "rb")
        post_data[jpg] = image_file

    return post_data


def get_absolute_path(subdirectory):
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), subdirectory)


class TestWaterSubmission(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="bob")
        absolute_path = get_absolute_path("forms")
        open_forms = open_all_files(absolute_path)
        self.json = '{"default_language": "default", ' \
                    '"id_string": "Water_2011_03_17", "children": [], ' \
                    '"name": "Water_2011_03_17", ' \
                    '"title": "Water_2011_03_17", "type": "survey"}'
        for path, open_file in open_forms.items():
            xform = XForm.objects.create(
                xml=open_file.read(), user=self.user, json=self.json)
            open_file.close()

        self._create_water_translated_form()

    def _create_water_translated_form(self):
        f = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Water_Translated_2011_03_10.xml"
        ))
        xml = f.read()
        f.close()
        XForm.objects.create(xml=xml, user=self.user, json=self.json)

    def test_form_submission(self):
        # no more submission to non-existent form,
        # setUp ensures the Water_Translated_2011_03_10 xform is valid
        f = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Water_Translated_2011_03_10_2011-03-10_14-38-28.xml"))
        xml = f.read()
        f.close()
        Instance.objects.create(xml=xml, user=self.user)

    def test_data_submission(self):
        subdirectories = ["Water_2011_03_17_2011-03-17_16-29-59"]
        for subdirectory in subdirectories:
            path = get_absolute_path(subdirectory)
            postdata = create_post_data(path)
            response = self.client.post('/bob/submission', postdata)
            self.failUnlessEqual(response.status_code, 201)

    def test_submission_for_missing_form(self):
        xml_file = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Health_2011_03_13_invalid_id_string.xml"
        ))
        postdata = {"xml_submission_file": xml_file}
        response = self.client.post('/bob/submission', postdata)
        self.failUnlessEqual(response.status_code, 404)
