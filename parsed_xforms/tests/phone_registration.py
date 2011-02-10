from django.test import TestCase
from xform_manager.models import Instance, XForm
from phone_manager.models import Phone

def text(filename):
    f = open(filename)
    result = f.read()
    f.close()
    return result

class PhoneTestCase(TestCase):
    def setUp(self):
        self.xform, created = XForm.objects.get_or_create(xml=text(
                "parsed_xforms/fixtures/test_forms/phone/"
                "forms/Phone.xml"
                ))
        self.instance, created = Instance.objects.get_or_create(xml=text(
                "parsed_xforms/fixtures/test_forms/phone/"
                "instances/Phone_2011-02-04_00-10-34.xml"
                ))

    def test_phone_created(self):
        d = {
            "imei" : "354059021882640",
            "visible_id" : "002",
            "phone_number" : "609 902 4682",
            "status" : "fuctional",
            "note" : None,
            }
        phone = Phone.objects.get(imei=d["imei"])
        for k, v in d.items():
            self.assertEqual(getattr(phone, k), v)
