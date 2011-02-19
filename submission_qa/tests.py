"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

from submission_qa.models import QualityReview
from parsed_xforms.models import ParsedInstance
from django.contrib.auth.models import User

class SimpleReviewTest(TestCase):
    def setUp(self):
        self.user1 = User(username="aggy")
        self.user2 = User(username="gwendolyn")
        
#        self.instance1 = ParsedInstance.objects.all()[0]
    
    def test_reviews_can_be_created(self):
        """
        tests that a user can create a review for a submission
        """
#        first_review = QualityReview(submission=self.instance1, \
#                                user=self.user1, \
#                                score=8)
#        first_review.save()
        #need some stuff before I can do this...
