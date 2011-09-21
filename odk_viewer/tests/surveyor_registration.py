"""
Testing POSTs to "/submission"
"""
from django.test import TestCase, Client

from odk_logger.models import Instance, XForm
from surveyor_manager.models import Surveyor
from datetime import datetime
from odk_logger.factory import XFormManagerFactory

xform_factory = XFormManagerFactory()

class TestSurveyorRegistration(TestCase):
    def setUp(self):
        [xf.delete() for xf in XForm.objects.all()]
        self.xf = xform_factory.create_registration_xform()
    
    def tearDown(self):
        self.xf.delete()

    def test_registration_form_loaded(self):
        registration_forms = XForm.objects.filter(title=u"registration")
        self.assertTrue(len(registration_forms) > 0)
    
    def test_registration_creates_surveyor(self):
        registration_instance = xform_factory.create_registration_instance({u'start': datetime.now(),
            u'name': u'Steak Sauce',
            u'device_id': u'12345'
            })
        
        self.assertEqual(Surveyor.objects.count(), 1)
        self.assertEqual(Surveyor.objects.all()[0].name, u"Steak Sauce")
        
    def test_multiple_registrations_on_the_same_phone(self):
        """
        Two users registered to phone '12345'.
            1: Betty (hour 1)
            2: Alex (hour 2)
        One submission:
            1. WaterSimple (hour 3)

        Submission should be attributed to "Alex Adams"
        """
        water = xform_factory.create_simple_xform()
        
        now = datetime.now()
        ordered_times = [datetime(now.year, now.month, now.day, 1), \
                        datetime(now.year, now.month, now.day, 2), \
                        datetime(now.year, now.month, now.day, 3)]
        first_registration = xform_factory.create_registration_instance({u'start': ordered_times[0], \
            u'name': u'Betty Bimbob', u'sex': u'female', \
            u'birth_date': u'1970-07-07', u'device_id': u'12345'})
        
        second_registration = xform_factory.create_registration_instance({u'start': ordered_times[1], \
            u'name': u'Alex Adams', u'birth_date': u'1986-08-15', \
            u'device_id': u'12345'})
        
        self.assertTrue(Surveyor.objects.count(), 2)
        
        submission = xform_factory.create_simple_instance({u'start': ordered_times[2]})
        
        self.assertTrue(submission.parsed_instance.surveyor is not None)
        self.assertEqual(submission.parsed_instance.surveyor.name, u'Alex Adams')
        
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
        water = xform_factory.create_simple_xform()
        
        now = datetime.now()
        ordered_times = [datetime(now.year, now.month, now.day, 1), \
                        datetime(now.year, now.month, now.day, 2), \
                        datetime(now.year, now.month, now.day, 3), \
                        datetime(now.year, now.month, now.day, 4)]
        
        user_one = xform_factory.create_registration_instance({u'form_id': self.xf.id_string, \
            u'start': ordered_times[0], u'name': u'Betty Bimbob', u'sex': u'female', \
            u'birth_date': u'1970-07-07', u'device_id': u'12345'})

        user_two = xform_factory.create_registration_instance({u'form_id':self.xf.id_string, \
            u'start': ordered_times[2], \
            u'name': u'Alex Adams', u'birth_date': u'1986-08-15', \
            u'device_id': u'12345'})
        
        self.assertTrue(Surveyor.objects.count(), 2)
        
        # submissions are sometimes parsed out of order, so we are saving the 2nd submission first
        submission_two = xform_factory.create_simple_instance({u'start': ordered_times[3]})
        
        submission_one = xform_factory.create_simple_instance({u'start': ordered_times[1]})

        self.assertEqual(submission_one.parsed_instance.phone.imei, u"12345")
        self.assertEqual(submission_one.parsed_instance.start_time, ordered_times[1])
        self.assertEqual(submission_one.parsed_instance.surveyor.name, u'Betty Bimbob')
        self.assertEqual(submission_two.parsed_instance.surveyor.name, u'Alex Adams')
