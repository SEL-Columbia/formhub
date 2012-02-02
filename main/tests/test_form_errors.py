from test_base import MainTestCase
from odk_logger.models import XForm
from django.core.urlresolvers import reverse
from odk_viewer.views import xls_export
import os

class TestFormErrors(MainTestCase):

    def test_bad_id_string(self):
        self._create_user_and_login()
        count = XForm.objects.count()
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.bad_id.xls")
        response = self._publish_xls_file(xls_path)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(XForm.objects.count(), count)

    def test_dl_no_xls(self):
        count = XForm.objects.count()
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.xls")
        response = self._publish_xls_file(xls_path)
        self.assertEquals(response.status_code, 200)
        self.xform = XForm.objects.all()[0]
        self.xform.shared_data = True
        self.xform.save()
        path = os.path.join('media', self.xform.xls.path)
        self.assertEqual(os.path.exists(path), True)
        os.remove(path)
        self.assertEqual(os.path.exists(path), False)
        url = reverse(xls_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 200)

    def test_dl_xls_not_file(self):
        count = XForm.objects.count()
        xls_path = os.path.join(self.this_directory, "fixtures",
                "transportation", "transportation.xls")
        response = self._publish_xls_file(xls_path)
        self.assertEquals(response.status_code, 200)
        self.xform = XForm.objects.all()[0]
        self.xform.xls = "blah"
        self.xform.save()
        url = reverse(xls_export, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})
        response = self.anon.get(url)
        self.assertEqual(response.status_code, 405)

