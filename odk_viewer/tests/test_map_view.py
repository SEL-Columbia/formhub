from django.test import TestCase
from django.core.urlresolvers import reverse
import odk_logger


class TestMapView(TestCase):
    def test_jsonform_url(self):
        id_string = "tutorial"
        username = "bob"
        url = reverse(odk_logger.views.download_jsonform, kwargs={"username": username, "id_string":id_string})
        self.assertIn("{0}/forms/{1}/form.json".format(username, id_string), url)
