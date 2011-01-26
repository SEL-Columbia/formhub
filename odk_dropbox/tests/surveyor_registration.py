"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client

from odk_dropbox.models import Instance, Surveyor, XForm
from xml.dom import minidom
from datetime import datetime

class TestSurveyorRegistration(TestCase):

    def test_registration_form_loaded(self):
        xf = load_xform_from_file("odk_dropbox/fixtures/test_forms/registration/forms/test_registration.xml")
        registration_forms = XForm.objects.filter(title="Registration")
        self.assertTrue(len(registration_forms) > 0)
    
    def test_registration_creates_surveyor(self):
        xf = load_xform_from_file("odk_dropbox/fixtures/test_forms/registration/forms/test_registration.xml")

        registration_instance = load_registration_with_values({'form_id':xf.id_string, \
            'start_time': datetime.now(),
            'name': 'Steak Sauce',
            'device_id': '12345'
            })
        registration_instance.save()
        
        self.assertTrue(Surveyor.objects.count(), 1)
        self.assertEqual(Surveyor.objects.all()[0].name(), "Steak Sauce")
        
    def test_multiple_registrations_on_the_same_phone(self):
        """
        Two users registered to phone '12345'.
            1: Betty (2 days ago)
            2: Alex (1 day ago)
        One submission:
            1. WaterSimple (1 hour ago)

        Submission should be attributed to "Alex Adams"
        """
        xf = load_xform_from_file("odk_dropbox/fixtures/test_forms/registration/forms/test_registration.xml")
        water =  load_xform_from_file("odk_dropbox/fixtures/test_forms/water_simple/forms/WaterSimple.xml")
        
        now = datetime.now()
        one_day_ago = datetime(now.year, now.month, now.day-1)
        two_days_ago = datetime(now.year, now.month, now.day-2)
        
        first_registration = load_registration_with_values({'form_id': xf.id_string, \
            'start_time': two_days_ago, 'name': 'Betty', 'sex': 'female', \
            'birth_date': '1970-07-07', 'device_id': '12345'})
        first_registration.save()
        
        second_registration = load_registration_with_values({'form_id':xf.id_string, \
            'start_time': one_day_ago, \
            'name': 'Alex Adams', 'birth_date': '1986-08-15', \
            'device_id': '12345'})
        second_registration.save()

        self.assertTrue(Surveyor.objects.count(), 2)
        
        submission = load_simple_submission({'start_time': now})
        submission.save()

        self.assertTrue(submission.surveyor is not None)
        self.assertEqual(submission.surveyor.name(), 'Alex Adams')

"""
fix everything below this line some day
----------------------------------------
"""

XFORM_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000"

def load_xform_from_file(filename):
    xf = XForm(xml=open(filename).read())
    xf.save()
    return xf

def load_simple_submission(custom_values):
    values = {
        'form_id': 'build_WaterSimple_1295821382',
        'name': 'Site Name',
        'value': '20',
        'device_id': '12345',
        'start_time': '2011-01-01T09:50:06.966',
        'end_time': '2011-01-01T09:53:22.965',
        'geopoint': '40.765102558006795 -73.97389419555664 300.0 4.0',
    }
    if 'start_time' in custom_values:
        st = custom_values['start_time']
        custom_values['start_time'] = st.strftime(XFORM_TIME_FORMAT)
        
        #if no end_time is specified, defaults to 1 hour
        values['end_time'] = datetime(st.year, st.month, st.day, st.hour+1).strftime(XFORM_TIME_FORMAT)
    
    if 'end_time' in custom_values:
        custom_values['end_time'] = custom_values['end_time'].strftime(XFORM_TIME_FORMAT)
    
    values.update(custom_values)
    subm = open("odk_dropbox/fixtures/test_forms/water_simple/instances/blank.xml").read()
    for key in values.keys():
        pattern = "#%s#" % key.upper()
        subm = subm.replace(pattern, values[key])
    return Instance(xml=subm)

def load_registration_with_values(custom_values):
    """
    A hacky way to load values into an XForm, but it *works*. Let's replace this
    when we can find a way to do this better.
    
    values are set to default and overridden by custom_values.
    """
    values = {'device_id': '12345',
        'form_id': 'Registration 2010-12-04_09-34-00',
        'start_time': '2011-01-01T09:50:06.966',
        'end_time': '2011-01-01T09:53:22.965',
        'name': 'Alexander',
        'sex': 'male',
        'birth_date': '1986-08-15',
        'languages': 'English'
    }
    if 'start_time' in custom_values:
        st = custom_values['start_time']
        custom_values['start_time'] = st.strftime(XFORM_TIME_FORMAT)
        
        #if no end_time is specified, defaults to 1 hour
        values['end_time'] = datetime(st.year, st.month, st.day, st.hour+1).strftime(XFORM_TIME_FORMAT)
    
    if 'end_time' in custom_values:
        custom_values['end_time'] = custom_values['end_time'].strftime(XFORM_TIME_FORMAT)
    
    values.update(custom_values)
    registration_xml_template = open('odk_dropbox/fixtures/test_forms/registration/instances/blank_registration.xml').read()
    for key in values.keys():
        pattern = "#%s#" % key.upper()
        registration_xml_template = registration_xml_template.replace(pattern, values[key])
    return Instance(xml=registration_xml_template)
