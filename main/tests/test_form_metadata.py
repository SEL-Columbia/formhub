import os
import hashlib

from test_base import MainTestCase
from main.models import MetaData
from main.views import show, edit, download_metadata, download_media_data,\
    delete_metadata

from django.core.files.base import File
from django.core.urlresolvers import reverse


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
        if data_type == 'media':
            name = 'screenshot.png'
        else:
            name = 'transportation.xls'
        path = os.path.join(self.this_directory, "fixtures",
                "transportation", name)
        with open(path) as doc_file:
            self.post_data = {}
            self.post_data[data_type] = doc_file
            response = self.client.post(self.edit_url, self.post_data)
        if data_type == 'media':
            self.doc = MetaData.objects.filter(data_type='media').reverse()[0]
            self.doc_url = reverse(download_media_data, kwargs={
                'username': self.user.username,
                'id_string': self.xform.id_string,
                'data_id': self.doc.id})
        else:
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

    def test_adds_supporting_media_on_submit(self):
        count = len(MetaData.objects.filter(xform=self.xform,
                data_type='media'))
        name = self._add_metadata(data_type='media')
        self.assertEquals(count + 1, len(
                MetaData.objects.filter(xform=self.xform,
                data_type='media')))

    def test_adds_mapbox_layer_on_submit(self):
        count = len(MetaData.objects.filter(xform=self.xform,
                data_type='mapbox_layer'))
        self.post_data = {}
        self.post_data['map_name'] = 'test_mapbox_layer'
        self.post_data['link'] = 'http://0.0.0.0:8080'
        response = self.client.post(self.edit_url, self.post_data)
        self.assertEquals(count + 1, len(
                MetaData.objects.filter(xform=self.xform,
                data_type='mapbox_layer')))

    def test_shows_supporting_doc_after_submit(self):
        name = self._add_metadata()
        response = self.client.get(self.url)
        self.assertContains(response, name)
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, name)

    def test_shows_supporting_media_after_submit(self):
        name = self._add_metadata(data_type='media')
        response = self.client.get(self.url)
        self.assertContains(response, name)
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, name)

    def test_shows_mapbox_layer_after_submit(self):
        self.post_data = {}
        self.post_data['map_name'] = 'test_mapbox_layer'
        self.post_data['link'] = 'http://0.0.0.0:8080'
        response = self.client.post(self.edit_url, self.post_data)
        response = self.client.get(self.url)
        self.assertContains(response, 'test_mapbox_layer')
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_mapbox_layer')

    def test_download_supporting_doc(self):
        name = self._add_metadata()
        response = self.client.get(self.doc_url)
        self.assertEqual(response.status_code, 200)
        fileName, ext = os.path.splitext(response['Content-Disposition'])
        self.assertEqual(ext, '.xls')

    def test_no_download_supporting_doc_for_anon(self):
        name = self._add_metadata()
        response = self.anon.get(self.doc_url)
        self.assertEqual(response.status_code, 403)

    def test_download_supporting_media(self):
        name = self._add_metadata(data_type='media')
        response = self.client.get(self.doc_url)
        self.assertEqual(response.status_code, 200)
        fileName, ext = os.path.splitext(response['Content-Disposition'])
        self.assertEqual(ext, '.png')

    def test_shared_download_supporting_doc_for_anon(self):
        name = self._add_metadata()
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.doc_url)
        self.assertEqual(response.status_code, 200)

    def test_shared_download_supporting_media_for_anon(self):
        name = self._add_metadata(data_type='media')
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.doc_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_supporting_doc(self):
        count = MetaData.objects.filter(xform=self.xform,
            data_type='supporting_doc').count()
        name = self._add_metadata()
        self.assertEqual(MetaData.objects.filter(xform=self.xform,
            data_type='supporting_doc').count() , count + 1)
        doc = MetaData.objects.filter(data_type='supporting_doc').reverse()[0]
        self.delete_doc_url = reverse(delete_metadata, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'data_id': doc.id})
        response = self.client.get(self.delete_doc_url + '?del=true')
        self.assertEqual(MetaData.objects.filter(xform=self.xform,
            data_type='supporting_doc').count(), count)
        self.assertEqual(response.status_code, 302)

    def test_delete_supporting_media(self):
        count = MetaData.objects.filter(xform=self.xform,
            data_type='media').count()
        name = self._add_metadata(data_type='media')
        self.assertEqual(MetaData.objects.filter(xform=self.xform,
            data_type='media').count(), count + 1)
        response = self.client.get(self.doc_url + '?del=true')
        self.assertEqual(MetaData.objects.filter(xform=self.xform,
            data_type='media').count(), count)
        self.assertEqual(response.status_code, 302)
        name = self._add_metadata(data_type='media')
        response = self.anon.get(self.doc_url + '?del=true')
        self.assertEqual(MetaData.objects.filter(xform=self.xform,
            data_type='media').count(), count + 1)
        self.assertEqual(response.status_code, 403)

    def _add_mapbox_layer(self):
        # check mapbox_layer metadata count
        self.count = len(MetaData.objects.filter(xform=self.xform,
            data_type='mapbox_layer'))
        # add mapbox_layer metadata
        post_data = {'map_name': 'test_mapbox_layer',
                     'link': 'http://0.0.0.0:8080'}
        response = self.client.post(self.edit_url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(MetaData.objects.filter(xform=self.xform,
            data_type='mapbox_layer')), self.count + 1)

    def test_delete_mapbox_layer(self):
        self._add_mapbox_layer()
        # delete mapbox_layer metadata
        doc = MetaData.objects.filter(data_type='mapbox_layer').reverse()[0]
        self.delete_doc_url = reverse(delete_metadata, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'data_id': doc.id})
        response = self.client.get(self.delete_doc_url + '?map_name_del=true')
        self.assertEqual(len(MetaData.objects.filter(xform=self.xform,
            data_type='mapbox_layer')), self.count)
        self.assertEqual(response.status_code, 302)

    def test_anon_delete_mapbox_layer(self):
        self._add_mapbox_layer()
        doc = MetaData.objects.filter(data_type='mapbox_layer').reverse()[0]
        self.delete_doc_url = reverse(delete_metadata, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'data_id': doc.id})
        response = self.anon.get(self.delete_doc_url + '?map_name_del=true')
        self.assertEqual(len(MetaData.objects.filter(xform=self.xform,
            data_type='mapbox_layer')), self.count + 1)
        self.assertEqual(response.status_code, 302)

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

    def test_media_file_hash(self):
        name = "screenshot.png"
        media_file = os.path.join(
            self.this_directory, 'fixtures', 'transportation', name)
        m = MetaData.objects.create(
            data_type='media', xform=self.xform, data_value=name,
            data_file=File(open(media_file), name),
            data_file_type='image/png')
        f = open(media_file)
        media_hash = hashlib.md5(f.read()).hexdigest()
        f.close()
        meta_hash = m.hash
        self.assertEqual(meta_hash, media_hash)
