from django.test import TestCase

from uis_r_us.views import get_nav_zones

class TestLgaList(TestCase):
    fixtures = ['lga.json', 'state.json', 'zone.json']

    def test_nav_zones(self):
        nav_zones = get_nav_zones()
        self.assertEqual(len(nav_zones), 6)
