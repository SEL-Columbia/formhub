
import os
import time

from django.core.urlresolvers import reverse
from pybamboo.connection import Connection
from pybamboo.dataset import Dataset

from main.views import show
from main.tests.test_base import MainTestCase
from odk_logger.models.xform import XForm
from restservice.views import add_service, delete_service
from restservice.RestServiceInterface import RestServiceInterface
from restservice.models import RestService


class RestServiceTest(MainTestCase):
    def setUp(self):
        self.service_url = u'http://0.0.0.0:8001/%(id_string)s/post/%(uuid)s'
        self.service_name = u'f2dhis2'
        self._create_user_and_login()
        filename = u'dhisform.xls'
        self.this_directory = os.path.dirname(__file__)
        path = os.path.join(self.this_directory, u'fixtures', filename)
        self._publish_xls_file(path)
        self.xform = XForm.objects.all().reverse()[0]

    def wait(self, t=1):
        time.sleep(t)

    def _create_rest_service(self):
        rs = RestService(service_url=self.service_url,
                         xform=self.xform, name=self.service_name)
        rs.save()
        self.restservice = rs

    def _add_rest_service(self, service_url, service_name):
        add_service_url = reverse(add_service, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.get(add_service_url, {})
        count = RestService.objects.all().count()
        self.assertEqual(response.status_code, 200)
        post_data = {'service_url': service_url,
                     'service_name': service_name}
        response = self.client.post(add_service_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(RestService.objects.all().count(), count + 1)

    def test_create_rest_service(self):
        count = RestService.objects.all().count()
        self._create_rest_service()
        self.assertEquals(RestService.objects.all().count(), count + 1)

    def test_service_definition(self):
        self._create_rest_service()
        sv = self.restservice.get_service_definition()()
        self.assertEqual(isinstance(sv, RestServiceInterface), True)

    def test_add_service(self):
        self._add_rest_service(self.service_url, self.service_name)

    def test_bamboo_service(self):
        bamboo_url = 'http://bamboo.io/'
        self._add_rest_service(bamboo_url, 'bamboo')
        self.wait(2)
        xml_submission1 = os.path.join(self.this_directory,
                                       u'fixtures',
                                       u'dhisform_submission1.xml')
        xml_submission2 = os.path.join(self.this_directory,
                                       u'fixtures',
                                       u'dhisform_submission2.xml')
        # make sure we got a bamboo_id
        self._make_submission(xml_submission1)
        self.assertEqual(self.response.status_code, 201)
        self.wait(5)
        xform = XForm.objects.get(id=self.xform.id)
        self.assertTrue(xform.bamboo_dataset)

        # make sure update went trhought by counting rows on bamboo
        self._make_submission(xml_submission2)
        self.assertEqual(self.response.status_code, 201)
        self.wait(2)
        dataset = Dataset(connection=Connection(bamboo_url),
                          dataset_id=xform.bamboo_dataset)
        self.assertEqual(dataset.get_info()['num_rows'], 2)

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
                         '"#restservice_tab">Rest Services</h3>'
                         in response.content)

    def test_delete_service(self):
        self._add_rest_service(self.service_url, self.service_name)
        count = RestService.objects.all().count()
        service = RestService.objects.reverse()[0]
        post_data = {'service-id': service.pk}
        del_service_url = reverse(delete_service, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.post(del_service_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            RestService.objects.all().count(), count - 1
        )
