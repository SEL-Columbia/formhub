"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)

__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}

# I was using this to test add_to_eav visually
# from controller.models import add_to_eav
# from odk_dropbox.models import Submission
# from eav.models import Value
# Value.objects.all().delete()
# s = Submission.objects.all()[0]
# add_to_eav(s)
