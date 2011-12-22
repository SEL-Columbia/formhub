from test_base import MainTestCase
from test_process import TestSite
from main.models import UserProfile
from odk_logger.views import show
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
import os

class TestFormShow(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        xls_path = os.path.join(self.this_directory, "fixtures", "transportation", "transportation.xls")
        self._publish_xls_file(xls_path)
        self.assertEqual(XForm.objects.count(), 1)
        self.xform = XForm.objects.all()[0]
        self.url = reverse(show, kwargs={'username': self.user.username, 'id_string': self.xform.id_string})

    def test_show_form_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)

    def test_hide_from_not_user(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_show_to_not_user_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)

    def test_show_private_if_shared_but_not_data(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)
        self.assertContains(response, 'PRIVATE')

    def test_show_link_if_shared_and_not_data(self):
        self.xform.shared = True
        self.xform.shared_data = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)
        self.assertContains(response, '/%s/data.csv' % self.xform.id_string)

