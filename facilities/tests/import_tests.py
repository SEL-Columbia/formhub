from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from facilities.data_loader import DataLoader


class BasicDataTest(TestCase):

    def test_limited_import(self):
        data_loader = DataLoader(limit_import=True)
        data_loader.load()
        expected_info = {
            "number of facilities": 41,
            "unused variables": [],
            "facilities without lgas": 0,
            "number of lga records": 183,
            "number of facility records": 4419
            }
        self.assertEquals(data_loader.get_info(), expected_info)

    def count_all_objects(self):
        result = {}
        for ct in ContentType.objects.all():
            result[ct.natural_key()] = ct.model_class().objects.count()
        return result
