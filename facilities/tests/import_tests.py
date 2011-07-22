from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from facilities.data_loader import DataLoader


class BasicDataTest(TestCase):

    def test_limited_import(self):
        data_loader = DataLoader(limit_import=True)
        data_loader.load()
        expected_info = {
            "number of facilities": 41, 
            "unused variables": [
                "education_proportion_of_schools_with_power", 
                "fees_paid_for_by_school_none", 
                "gap_primary_schools_potable_water", 
                "num_primary_schools_with_potable_water"
                ], 
            "facilities without lgas": 0, 
            "number of lga records": 180, 
            "number of facility records": 4234
            }
        self.assertEquals(data_loader.get_info(), expected_info)

    def count_all_objects(self):
        result = {}
        for ct in ContentType.objects.all():
            result[ct.natural_key()] = ct.model_class().objects.count()
        return result
