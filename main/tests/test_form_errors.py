from test_base import MainTestCase
from odk_logger.models import XForm
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

