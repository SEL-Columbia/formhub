from django.db.models import Sum
from django.test import TestCase
from stats.models import StatsCount


class StatsTest(TestCase):

    def setUp(self):
        pass

    def test_statscount(self):
        StatsCount.objects.create(key="*", value=1)
        self.assertEqual(
            StatsCount.objects.aggregate(Sum('value'))['value__sum'], 1)