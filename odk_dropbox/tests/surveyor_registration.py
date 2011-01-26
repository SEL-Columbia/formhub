"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client

from odk_dropbox.models import Instance, Surveyor, XForm
from xml.dom import minidom
from datetime import datetime

XFORM_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000"

class TestSurveyorRegistration(TestCase):

    def test_registration_form_loaded(self):
        xf = load_xform_from_file("odk_dropbox/fixtures/test_forms/registration/forms/test_registration.xml")
        registration_forms = XForm.objects.filter(title="Registration")
        self.assertTrue(len(registration_forms) > 0)
    
    def test_registration_creates_surveyor(self):
        xf = load_xform_from_file("odk_dropbox/fixtures/test_forms/registration/forms/test_registration.xml")
        form_id = xf.id_string
        
        registration_instance = load_registration_with_values({'form_id':form_id, \
            'start_time': datetime.now(),
            'name': 'Steak Sauce'
            })
        registration_instance.save()
        self.assertTrue(Surveyor.objects.count(), 1)
        self.assertEqual(Surveyor.objects.all()[0].name(), "Steak Sauce")
        
    # test_submissions_are_attributed_to_correct_surveyor
    # ...and many others

def load_xform_from_file(filename):
    xf = XForm(xml=open(filename).read())
    xf.save()
    return xf

def load_registration_with_values(custom_values):
    """
    A hacky way to load values into an XForm, but it *works*. Let's replace this
    when we can find a way to do this better.
    
    values are set to default and overridden by custom_values.
    """
    values = {'device_id': '4894943',
        'form_id': 'Registration 2010-12-04_09-34-00',
        'start_time': '2011-01-01T09:50:06.966',
        'end_time': '2011-01-01T09:53:22.965',
        'name': 'Alexander',
        'sex': 'male',
        'birth_date': '1986-08-15',
        'languages': 'English',
        'phone_id': '026',
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
