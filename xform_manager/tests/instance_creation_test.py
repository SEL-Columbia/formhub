from django.test import TestCase, Client
from xform_manager.models import XForm, Instance
import os, glob

def open_all_files(path):
    file_paths = glob.glob( os.path.join(path, "*") )
    result = {}
    for file_path in file_paths:
        if file_path.endswith(".jpg"):
            # note the "rb" mode is to open a binary file
            result[file_path] = open(file_path, "rb")
        else:
            result[file_path] = open(file_path)
    return result

def create_post_data(path):
    xml_files = glob.glob( os.path.join(path, "*.xml") )
    if len(xml_files)!=1:
        raise Exception("There should be a single XML file in this directory.")
    xml_file = open(xml_files[0])
    post_data = {"xml_submission_file" : xml_file}

    for jpg in glob.glob(os.path.join(path, "*.jpg")):
        # note the "rb" mode is to open a binary file
        image_file = open(jpg, "rb")
        post_data[jpg] = image_file

    return post_data

def get_absolute_path(subdirectory):
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        subdirectory
        )


class TestWaterSubmission(TestCase):

    def setUp(self):
        absolute_path = get_absolute_path("forms")
        open_forms = open_all_files(absolute_path)
        for path, open_file in open_forms.items():
            XForm.objects.create(xml=open_file.read())
            open_file.close()

    def test_xform_creation(self):
        f = open(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Water_Translated_2011_03_10.xml"
                ))
        xml = f.read()
        f.close()
        xform = XForm.objects.create(
            xml=xml
            )

    def test_form_submission(self):
        f = open(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Water_Translated_2011_03_10_2011-03-10_14-38-28.xml"
                ))
        xml = f.read()
        f.close()
        instance = Instance.objects.create(
            xml=xml
            )

    def test_instance_creation(self):
        xml_file = open(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Health_2011_03_13.xml_2011-03-15_20-30-28",
                "Health_2011_03_13.xml_2011-03-15_20-30-28.xml"
                ))
        # note the "rb" mode is to open a binary file
        image_file = open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "Health_2011_03_13.xml_2011-03-15_20-30-28",
                "1300221157303.jpg"),
            "rb")

        # ODK Collect uses the name of the jpg file as the key in the
        # post.
        postdata = {"xml_submission_file" : xml_file,
                    "1300221157303.jpg" : image_file}
        response = self.client.post('/submission', postdata)
        self.failUnlessEqual(response.status_code, 201)

    def test_data_submission(self):
        subdirectories = ["Water_2011_03_17_2011-03-17_16-29-59"]
        for subdirectory in subdirectories:
            path = get_absolute_path(subdirectory)
            postdata = create_post_data(path)
            response = self.client.post('/submission', postdata)
            self.failUnlessEqual(response.status_code, 201)
