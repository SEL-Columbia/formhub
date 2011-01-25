"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client

from ipdb import set_trace as debug


from odk_dropbox.models import Instance, Surveyor

class TestSurveyorRegistration(TestCase):
    def test_registration_xml_received(self):
        """
        A sample registration survey can be received
        """

        post_data = {
            "xml_submission_file" : (
                "Registration_2011-1-1_10-00-00.xml",
                sample_registration_xml({'form_id': 'Registration_2011-1-1_10-00-00'})
            )
        }
        response = self.client.post("/submission", post_data)
        self.assertEqual(Surveyor.objects.count(), 1)
    
    # def test_registration_creates_surveyor(self):
    #     pass
    # def test_xforms_attributed_to_correct_surveyor(self):
    #     pass


import re
def sample_registration_xml(passed_vals):
    """
    A quick hack to get a form that can be customized and submitted to register surveyors.
    """
    default_values = {'form_id': 'Registration_2010-12-07_11-18-59', \
        'device_id': '351771047024444', 'phone_number': '4158867537', \
        'start_time': '2010-12-07T11:18:59.945', 'end_time': '2010-12-11T07:53:11.938', \
        'name': 'Alexander', 'sex':'male', 'birth_date': '1986-08-15', \
        'languages': 'English', 'phone_id': '123'
    }
    values = default_values
    values.update(passed_vals)
    # does python have key-value interpolation?. anyways, this is most definitely not
    # the right way to do this, but it WORKS! (hopefully)
    survey = """
    <?xml version='1.0' ?>
    <registration id="%s">
        <device_id>%s</device_id>
        <phone_number>%s</phone_number>
        <start>%s</start>
        <end>%s</end>
        <name>%s</name>
        <sex>%s</sex>
        <birth_date>%s</birth_date>
        <languages>%s</languages>
        <phone_id>%s</phone_id>
    </registration>
    """ % (values['form_id'], values['device_id'], \
            values['phone_number'], values['start_time'], \
            values['end_time'], values['name'], values['sex'], \
            values['birth_date'], values['languages'], \
            values['phone_id'])
    #take out the spaces
    return re.sub(r"\s+(.*)\s*", r"\1", survey)

