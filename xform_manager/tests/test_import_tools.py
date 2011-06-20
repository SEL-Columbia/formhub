from django.test import TestCase, Client
from xform_manager.models import XForm, Instance
import os, glob

from django.core.management import call_command

CUR_PATH = os.path.abspath(__file__)
CUR_DIR = os.path.dirname(CUR_PATH)
DB_FIXTURES_PATH = os.path.join(CUR_DIR, 'data_from_sdcard')

from django.conf import settings

def images_count():
    return len(glob.glob(os.path.join(settings.MEDIA_ROOT, 'attachments', '*')))

class TestImportingDatabase(TestCase):
    def test_importing_b1_and_b2(self):
        """
        b1 and b2 are from the *same phone* at different times. (this might not be a realistic test)
        
        b1:
        1 photo survey (completed)
        1 simple survey (not marked complete)

        b2:
        1 photo survey (duplicate, completed)
        1 simple survey (marked as complete)
        """

        i = Instance.objects.count()
        ims = images_count()
        
        call_command('import_tools', DB_FIXTURES_PATH)
        
        i2 = Instance.objects.count()
        ims2 = images_count()
        
        #Images are not duplicated
        self.assertEqual(ims, ims2)
        
        # Instance count should have incremented 
        # by 1 (or 2) based on the b1 & b2 data sets
        self.assertTrue(i < i2)
    
    def test_importing_duplicate_instance(self):
        """
        The management command should not duplicate the survey that has already been submitted via web.
        """
        #xml_str is the completed simple fixture instance
        instance_id = "simple_two_questions_2011_05_03_2011-05-03_18-30-49"
        path_to_b2_instance = os.path.join(DB_FIXTURES_PATH, "b2", "odk", "instances", instance_id, "%s.xml" % instance_id)
        f = open(path_to_b2_instance)
        xml_str = f.read()
        f.close()
        Instance.objects.create(xml=xml_str)
        icount1 = Instance.objects.count()
        
        call_command('import_tools', DB_FIXTURES_PATH)
        
        icount2 = Instance.objects.count()

        #it should increment by 1 (the incomplete survey) I think??
        self.assertEqual(icount1+1, icount2)