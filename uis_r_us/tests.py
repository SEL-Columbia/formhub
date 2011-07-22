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
        nzs = [get_nav_zones(), get_nav_zones2()]

        def get_names(z):
            [n['name'] for n in z]
        self.assertEqual(*[get_names(nz) for nz in nzs])

        def state_names(z):
            return [s['name'] for s in z['states']]
        self.assertEqual(*[state_names(nz[0]) for nz in nzs])

        def ordered_lga_slugs(z):
            lga_slugs = []
            for s in z['states']:
                for lga in s['lgas']:
                    lga_slugs.append(lga['unique_slug'])
            lga_slugs.sort()
            return lga_slugs
        self.assertEqual(*[ordered_lga_slugs(nz[0]) for nz in nzs])
