from django.db.models import Sum
from django.test import TestCase
from stats.models import StatsCount
from stats.tasks import stat_log

class StatsTest(TestCase):

    def setUp(self):
        pass

    def test_statscount(self):
        StatsCount.objects.create(key="*", value=1)
        self.assertEqual(
            StatsCount.stats.count(key="*"), 1)

    def test_task_stat_log(self):
        result = stat_log.delay("*", 1)
        self.assertEqual(
            (result.get().key, result.get().value), (u"*", 1))
        self.assertTrue(result.successful())
