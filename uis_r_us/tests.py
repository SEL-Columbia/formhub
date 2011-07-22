from django.test import TestCase

from uis_r_us.views import get_nav_zones, get_nav_zones2

class TestLgaList(TestCase):
    fixtures = ['lga.json', 'state.json', 'zone.json']

    def test_nav_zones(self):
        nav_zones = get_nav_zones()
        self.assertEqual(len(nav_zones), 6)

    def test_nav_zones2(self):
        nav_zones2 = get_nav_zones2()
        self.assertEqual(len(nav_zones2), 6)

    def test_nav_zone_equality(self):
        nav_zones = get_nav_zones()
        nav_zones2 = get_nav_zones2()
        names1 = [n['name'] for n in nav_zones]
        names2 = [n['name'] for n in nav_zones2]
        self.assertEqual(names1, names2)