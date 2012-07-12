from django.core.urlresolvers import reverse
import os
from main.views import show
from main.tests.test_base import MainTestCase
from odk_logger.models.xform import XForm
from restservice.views import add_service
from restservice.RestServiceInterface import RestServiceInterface
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

    def _create_rest_service(self):
        rs = RestService(service_url=self.service_url,
            xform=self.xform, name=self.service_name)
        rs.save()
        self.restservice = rs

    def test_create_rest_service(self):
        count = RestService.objects.all().count()
        self._create_rest_service()
        self.assertEquals(RestService.objects.all().count(), count + 1)

    def  test_service_definition(self):
        self._create_rest_service()
        sv = self.restservice.get_service_definition()()
        self.assertEqual(isinstance(sv, RestServiceInterface), True)

    def test_add_service(self):
        add_service_url = reverse(add_service, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.get(add_service_url, {})
        count = RestService.objects.all().count()
        self.assertEqual(response.status_code, 200)
        post_data = {'service_url': self.service_url,
                     'service_name': self.service_name}
        response = self.client.post(add_service_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(RestService.objects.all().count(), count + 1)

    def test_anon_service_view(self):
        self.xform.shared = True
        self.xform.save()
        self._logout()
        url = reverse(show, kwargs={
            'username': self.xform.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.get(url)
        self.assertFalse('<h3 data-toggle="collapse" data-target='
                         '"#restservice_tab">Rest Services</h3>' \
                in response.content)