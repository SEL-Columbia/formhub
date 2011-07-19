from django.test import TestCase
from django.contrib.auth.models import User
from models import technical_assistants, \
    add_user_to_groups_based_on_email_address
from django.db.models.signals import post_save


class SignalTest(TestCase):

    def test_signal_being_fired(self):
        self.fired = False
        def mark_signal_fired(sender, **kwargs):
            self.fired = True
        post_save.connect(mark_signal_fired, sender=User)
        carl = User.objects.create(
            username='carl', email='carl@gmail.com', password='blah'
            )
        self.assertTrue(self.fired)

    def test_assign_groups_in_receivers(self):
        self.assertTrue(
            add_user_to_groups_based_on_email_address in \
                [r[1]() for r in post_save.receivers]
            )

    def test_user_added_to_appropriate_group(self):
        allen = User.objects.create(
            username='allen', email='allen@mdgs.gov.ng', password='blah'
            )

        bob = User.objects.create(
            username='bob', email='bob@gmail.com', password='blah'
            )

        # TODO: Figure out why this test won't work while I have
        # confirmed the signal is being received in the django
        # shell. I believe there's something going on with the many to
        # many field during testing, very bizarre.
        self.assertTrue(technical_assistants in allen.groups.all())

        self.assertTrue(technical_assistants not in bob.groups.all())
