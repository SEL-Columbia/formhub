"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

from submission_qr.models import QualityReview
from parsed_xforms.models import ParsedInstance
from django.contrib.auth.models import User

import factory

class SimpleReviewTest(TestCase):
    def setUp(self):
        self.user1 = User(username="aggy")
        self.user2 = User(username="gwendolyn")
        self.xform_factory = factory.XFormManagerFactory()

        self.instance1 = self.xform_factory.create_simple_instance()
    
    def test_reviews_can_be_created(self):
        """
        tests that a user can create a review for a submission
        """
        self.assertEqual(0, QualityReview.objects.count())
        first_review = QualityReview(submission=self.instance1, \
                                reviewer=self.user1, \
                                score=8)
        first_review.save()

        self.assertEqual(1, QualityReview.objects.count())