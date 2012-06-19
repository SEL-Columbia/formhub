import os
from main.tests.test_base import MainTestCase
from odk_logger.models.xform import XForm
from restservice.models import RestService

class RestServiceTest(MainTestCase):
    def setUp(self):
        self.service_url = u'http://0.0.0.0:8001/%(id_string)s/post/%(uuid)s'
        self.service_name = u'f2dhis2'
        self._create_user_and_login()
        filename = u'dhisform.xls'
        this_directory = os.path.dirname(__file__)
        path = os.path.join(this_directory, u'fixtures' , filename)
        self._publish_xls_file(path)
        self.xform = XForm.objects.all().reverse()[0]

    def test_create_rest_service(self):
        count = RestService.objects.all().count()
        rs = RestService(service_url=self.service_url,
                        xform=self.xform, name=self.service_name)
        rs.save()
        self.assertEquals(RestService.objects.all().count(), count + 1)