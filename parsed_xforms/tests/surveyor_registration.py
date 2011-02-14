"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client

from xform_manager.models import Instance, XForm
from surveyor_manager.models import Surveyor
from datetime import datetime

class TestSurveyorRegistration(TestCase):

    def test_registration_form_loaded(self):
        xf = load_xform_from_xml_file("parsed_xforms/fixtures/test_forms/registration/forms/test_registration.xml")
        registration_forms = XForm.objects.filter(title="Registration")
        self.assertTrue(len(registration_forms) > 0)
    
    def test_registration_creates_surveyor(self):
        xf = load_xform_from_xml_file("parsed_xforms/fixtures/test_forms/registration/forms/test_registration.xml")

        registration_instance = load_registration_with_values({'form_id':xf.id_string, \
            'start_time': datetime.now(),
            'name': 'Steak Sauce',
            'device_id': '12345'
            })
        registration_instance.save()
        
        self.assertTrue(Surveyor.objects.count(), 1)
        self.assertEqual(Surveyor.objects.all()[0].name, "Steak Sauce")
        
    def test_multiple_registrations_on_the_same_phone(self):
        """
        Two users registered to phone '12345'.
            1: Betty (hour 1)
            2: Alex (hour 2)
        One submission:
            1. WaterSimple (hour 3)

        Submission should be attributed to "Alex Adams"
        """
        xf = load_xform_from_xml_file("parsed_xforms/fixtures/test_forms/registration/forms/test_registration.xml")
        water =  load_xform_from_xml_file("parsed_xforms/fixtures/test_forms/water_simple/forms/WaterSimple.xml")
        
        now = datetime.now()
        ordered_times = [datetime(now.year, now.month, now.day, 1), \
                        datetime(now.year, now.month, now.day, 2), \
                        datetime(now.year, now.month, now.day, 3)]
        
        first_registration = load_registration_with_values({'form_id': xf.id_string, \
            'start_time': ordered_times[0], 'name': 'Betty Bimbob', 'sex': 'female', \
            'birth_date': '1970-07-07', 'device_id': '12345'})
        first_registration.save()
        
        second_registration = load_registration_with_values({'form_id':xf.id_string, \
            'start_time': ordered_times[1], \
            'name': 'Alex Adams', 'birth_date': '1986-08-15', \
            'device_id': '12345'})
        second_registration.save()

        self.assertTrue(Surveyor.objects.count(), 2)
        
        submission = load_simple_submission({'start_time': ordered_times[2]})
        submission.save()

        self.assertTrue(submission.parsed_instance.surveyor is not None)
        self.assertEqual(submission.parsed_instance.surveyor.name, 'Alex Adams')
        
    def test_multiple_submissions_out_of_order(self):
        """
        Two users registered to phone '12345'.
        User    Submission
        --      --
        1: user_one (named Betty, hour 1)
                2. submission_one # hour 2 - should be attributed to betty 
        3: user_two (named Alex, hour 3)
                4. submission_two # hour 4 - should be attributed to alex
                
        Registrations performed in order,
        Submissions entered out of order.
        """
        xf = load_xform_from_xml_file("parsed_xforms/fixtures/test_forms/registration/forms/test_registration.xml")
        water =  load_xform_from_xml_file("parsed_xforms/fixtures/test_forms/water_simple/forms/WaterSimple.xml")

        now = datetime.now()
        ordered_times = [datetime(now.year, now.month, now.day, 1), \
                        datetime(now.year, now.month, now.day, 2), \
                        datetime(now.year, now.month, now.day, 3), \
                        datetime(now.year, now.month, now.day, 4)]
        
        user_one = load_registration_with_values({'form_id': xf.id_string, \
            'start_time': ordered_times[0], 'name': 'Betty Bimbob', 'sex': 'female', \
            'birth_date': '1970-07-07', 'device_id': '12345'})
        user_one.save()

        user_two = load_registration_with_values({'form_id':xf.id_string, \
            'start_time': ordered_times[2], \
            'name': 'Alex Adams', 'birth_date': '1986-08-15', \
            'device_id': '12345'})
        user_two.save()

        self.assertTrue(Surveyor.objects.count(), 2)


        # submissions are sometimes parsed out of order, so we are saving the 2nd submission first
        submission_two = load_simple_submission({'start_time': ordered_times[3]})
        submission_two.save()
        
        submission_one = load_simple_submission({'start_time': ordered_times[1]})
        submission_one.save()

        self.assertEqual(submission_one.parsed_instance.surveyor.name, 'Betty Bimbob')
        self.assertEqual(submission_two.parsed_instance.surveyor.name, 'Alex Adams')

"""
fix everything below this line some day
----------------------------------------
"""

XFORM_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000"

def load_xform_from_xml_file(filename):
    xf = XForm()
    xf.xml = open(filename).read()
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
    subm = open("parsed_xforms/fixtures/test_forms/water_simple/instances/blank.xml").read()
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
    registration_xml_template = open('parsed_xforms/fixtures/test_forms/registration/instances/blank_registration.xml').read()
    for key in values.keys():
        pattern = "#%s#" % key.upper()
        registration_xml_template = registration_xml_template.replace(pattern, values[key])
    return Instance(xml=registration_xml_template)
