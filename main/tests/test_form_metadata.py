from test_base import MainTestCase
from main.models import MetaData
from main.views import show, edit, download_metadata
from django.core.urlresolvers import reverse
import os

class TestFormMetadata(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self.edit_url = reverse(edit, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def _add_metadata(self, data_type='doc'):
        name = 'transportation.xls'
        path = os.path.join(self.this_directory, "fixtures",
                "transportation", name)
        with open(path) as doc_file:
            post_data = {}
            post_data[data_type] = doc_file
            response = self.client.post(self.edit_url, post_data)
        self.doc = MetaData.objects.all().reverse()[0]
        self.doc_url = reverse(download_metadata, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'data_id': self.doc.id})
        return name

    def test_adds_supporting_doc_on_submit(self):
        count = len(MetaData.objects.filter(xform=self.xform,
                data_type='supporting_doc'))
        name = self._add_metadata()
        self.assertEquals(count + 1, len(
                MetaData.objects.filter(xform=self.xform,
                data_type='supporting_doc')))

    def test_shows_supporting_doc_after_submit(self):
        name = self._add_metadata()
        response = self.client.get(self.url)
        self.assertContains(response, name)
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, name)

    def test_download_supporting_doc(self):
        name = self._add_metadata()
        response = self.client.get(self.doc_url)
        self.assertEqual(response.status_code, 200)

    def test_no_download_supporting_doc_for_anon(self):
        name = self._add_metadata()
        response = self.anon.get(self.doc_url)
        self.assertEqual(response.status_code, 403)

    def test_shared_download_supporting_doc_for_anon(self):
        name = self._add_metadata()
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.doc_url)
        self.assertEqual(response.status_code, 200)

    def test_user_source_edit_updates(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'source': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MetaData.source(self.xform).data_value, desc)

    def test_upload_source_file(self):
        name = self._add_metadata('source')
        self.assertNotEqual(MetaData.source(self.xform).data_file, None)

    def test_upload_source_file_set_value_to_name(self):
        name = self._add_metadata('source')
        self.assertEqual(MetaData.source(self.xform).data_value, name)

    def test_upload_source_file_keep_name(self):
        desc = 'Snooky'
        response = self.client.post(self.edit_url, {'source': desc},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        name = self._add_metadata('source')
        self.assertNotEqual(MetaData.source(self.xform).data_file, None)
        self.assertEqual(MetaData.source(self.xform).data_value, desc)
