import copy
import os
import sys
import time

from django.conf import Settings
from django.db.models.loading import cache, load_app
from django.utils.unittest import TestCase


class InstalledAppsGlobbingTest(TestCase):
    def setUp(self):
        self.OLD_SYS_PATH = sys.path[:]
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        self.OLD_TZ = os.environ.get("TZ")

    def test_globbing(self):
        settings = Settings('test_settings')
        self.assertEqual(settings.INSTALLED_APPS, ['parent.app', 'parent.app1', 'parent.app_2'])

    def tearDown(self):
        sys.path = self.OLD_SYS_PATH
        if hasattr(time, "tzset") and self.OLD_TZ:
            os.environ["TZ"] = self.OLD_TZ
            time.tzset()


class EggLoadingTest(TestCase):

    def setUp(self):
        self.old_path = sys.path[:]
        self.egg_dir = '%s/eggs' % os.path.dirname(__file__)

        # This test adds dummy applications to the app cache. These
        # need to be removed in order to prevent bad interactions
        # with the flush operation in other tests.
        self.old_app_models = copy.deepcopy(cache.app_models)
        self.old_app_store = copy.deepcopy(cache.app_store)

    def tearDown(self):
        sys.path = self.old_path
        cache.app_models = self.old_app_models
        cache.app_store = self.old_app_store

    def test_egg1(self):
        """Models module can be loaded from an app in an egg"""
        egg_name = '%s/modelapp.egg' % self.egg_dir
        sys.path.append(egg_name)
        models = load_app('app_with_models')
        self.assertFalse(models is None)

    def test_egg2(self):
        """Loading an app from an egg that has no models returns no models (and no error)"""
        egg_name = '%s/nomodelapp.egg' % self.egg_dir
        sys.path.append(egg_name)
        models = load_app('app_no_models')
        self.assertTrue(models is None)

    def test_egg3(self):
        """Models module can be loaded from an app located under an egg's top-level package"""
        egg_name = '%s/omelet.egg' % self.egg_dir
        sys.path.append(egg_name)
        models = load_app('omelet.app_with_models')
        self.assertFalse(models is None)

    def test_egg4(self):
        """Loading an app with no models from under the top-level egg package generates no error"""
        egg_name = '%s/omelet.egg' % self.egg_dir
        sys.path.append(egg_name)
        models = load_app('omelet.app_no_models')
        self.assertTrue(models is None)

    def test_egg5(self):
        """Loading an app from an egg that has an import error in its models module raises that error"""
        egg_name = '%s/brokenapp.egg' % self.egg_dir
        sys.path.append(egg_name)
        self.assertRaises(ImportError, load_app, 'broken_app')
        try:
            load_app('broken_app')
        except ImportError, e:
            # Make sure the message is indicating the actual
            # problem in the broken app.
            self.assertTrue("modelz" in e.args[0])
