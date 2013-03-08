from django.conf import settings
import os
from test_base import MainTestCase
from main.views import show, form_photos, update_xform, profile
from django.core.urlresolvers import reverse
from odk_logger.models import XForm
from odk_logger.views import download_xlsform, download_jsonform,\
    download_xform, delete_xform
from odk_viewer.views import export_list, map_view
from utils.user_auth import http_auth_string
from odk_viewer.models import ParsedInstance


class TestFormShow(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()
        self.url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })

    def test_show_form_name(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.xform.id_string)

    def test_hide_from_anon(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_hide_from_not_user(self):
        self._create_user_and_login("jo")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_show_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dl_xlsx_xlsform(self):
        self._publish_xlsx_file()
        response = self.client.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': 'exp_one'
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Disposition'],
            "attachment; filename=exp_one.xlsx")

    def test_dl_xls_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_dl_xls_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        response = self.anon.get(reverse(download_xlsform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), **extra)
        self.assertEqual(response.status_code, 200)

    def test_dl_json_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_dl_jsonp_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        callback = 'jsonpCallback'
        response = self.anon.get(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), {'callback': callback})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.startswith(callback + '('), True)
        self.assertEqual(response.content.endswith(')'), True)

    def test_dl_json_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        response = self.anon.get(reverse(download_jsonform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), **extra)
        self.assertEqual(response.status_code, 200)

    def test_dl_xform_to_anon_if_public(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(reverse(download_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))
        self.assertEqual(response.status_code, 200)

    def test_dl_xform_for_basic_auth(self):
        extra = {
            'HTTP_AUTHORIZATION': http_auth_string(self.login_username,
                self.login_password)
        }
        response = self.anon.get(reverse(download_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }), **extra)
        self.assertEqual(response.status_code, 200)

    def test_show_private_if_shared_but_not_data(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertContains(response, 'PRIVATE')

    def test_show_link_if_shared_and_data(self):
        self.xform.shared = True
        self.xform.shared_data = True
        self.xform.save()
        self._submit_transport_instance()
        response = self.anon.get(self.url)
        self.assertContains(response, reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'csv'
        }))

    def test_show_link_if_owner(self):
        self._submit_transport_instance()
        response = self.client.get(self.url)
        self.assertContains(response, reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'csv'
        }))
        self.assertContains(response, reverse(export_list, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
            'export_type': 'xls'
        }))
        self.assertNotContains(response, reverse(map_view, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        }))

        # check that a form with geopoints has the map url
        response = self._publish_xls_file(
            os.path.join(
                os.path.dirname(__file__), "fixtures", "gps", "gps.xls"))
        self.assertEqual(response.status_code, 200)
        self.xform = XForm.objects.latest('date_created')

        show_url = reverse(show, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        map_url = reverse(map_view, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        response = self.client.get(show_url)
        # check that map url doesnt show before we have submissions
        self.assertNotContains(response, map_url)

        # make a submission
        self._make_submission(
            os.path.join(
                os.path.dirname(__file__), "fixtures", "gps", "instances", "gps_1980-01-23_20-52-08.xml")
        )
        self.assertEqual(self.response.status_code, 201)

        # get new show view
        response = self.client.get(show_url)
        self.assertContains(response, map_url)

    def test_user_sees_edit_btn(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'edit</a>')

    def test_user_sees_settings(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Settings')

    def test_anon_no_edit_btn(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'edit</a>')

    def test_anon_no_toggle_data_share_btn(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'PUBLIC</a>')
        self.assertNotContains(response, 'PRIVATE</a>')

    def test_show_add_sourc_doc_if_owner(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Source document:')

    def test_show_add_supporting_docs_if_owner(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Supporting document:')

    def test_show_add_supporting_media_if_owner(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Media upload:')

    def test_show_add_mapbox_layer_if_owner(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'JSONP url:')

    def test_hide_add_supporting_docs_if_not_owner(self):
        self.xform.shared = True
        self.xform.save()
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'Upload')

    def test_load_photo_page(self):
        response = self.client.get(reverse(form_photos, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string}))
        self.assertEqual(response.status_code, 200)

    def test_load_from_uuid(self):
        self.xform = XForm.objects.get(pk=self.xform.id)
        response = self.client.get(reverse(show, kwargs={
            'uuid': self.xform.uuid}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                '%s%s' % (self.base_url, self.url))

    def test_xls_replace_markup(self):
        """
        Check that update form is only shown when there are no submissions and the user is the owner
        """
        # when we have 0 submissions, update markup exists
        self.xform.shared = True
        self.xform.save()
        dashboard_url = reverse(profile, kwargs={
            'username': 'bob'
        })
        response = self.client.get(dashboard_url)
        self.assertContains(response, 'href="#replace-transportation_2011_07_25"')
        # a non owner can't see the markup
        response = self.anon.get(self.url)
        self.assertNotContains(response, 'href="#replace-transportation_2011_07_25"')
        # when we have a submission, we cant update the xls form
        self._submit_transport_instance()
        response = self.client.get(dashboard_url)
        self.assertNotContains(response, 'href="#replace-transportation_2011_07_25"')

    def test_non_owner_cannot_replace_form(self):
        """
        Test that a non owner cannot replace a shared xls form
        """
        xform_update_url = reverse(update_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self.xform.shared = True
        self.xform.save()
        # create and login another user
        self._create_user_and_login('peter', 'peter')
        response = self.client.post(xform_update_url)
        # since we are logged in, we'll be re-directed to our profile page
        self.assertRedirects(response, self.base_url,
            status_code=302, target_status_code=302)

    def test_replace_xform(self):
        xform_update_url = reverse(update_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        count = XForm.objects.count()
        xls_path = os.path.join(self.this_directory, "fixtures",
            "transportation", "transportation_updated.xls")
        with open(xls_path, "r") as xls_file:
            post_data = {'xls_file': xls_file}
            response = self.client.post(xform_update_url, post_data)
        self.assertEqual(XForm.objects.count(), count)
        self.xform = XForm.objects.order_by('id').reverse()[0]
        data_dictionary = self.xform.data_dictionary()
        # look for the preferred_means question which is only in the updated xls
        is_updated_form = len([e.name for e in data_dictionary.survey_elements
                                 if e.name == u'preferred_means']) > 0
        self.assertTrue(is_updated_form)

    def test_xform_delete(self):
        id_string = self.xform.id_string
        form_exists = XForm.objects.filter(user=self.user,
            id_string = id_string).count() == 1
        self.assertTrue(form_exists)
        xform_delete_url = reverse(delete_xform, kwargs={
            'username': self.user.username,
            'id_string': id_string
        })
        self.client.post(xform_delete_url)
        form_deleted = XForm.objects.filter(user=self.user,
            id_string = id_string).count() == 0
        self.assertTrue(form_deleted)

    def test_non_owner_cant_delete_xform(self):
        id_string = self.xform.id_string
        form_exists = XForm.objects.filter(user=self.user,
            id_string = id_string).count() == 1
        self.assertTrue(form_exists)
        xform_delete_url = reverse(delete_xform, kwargs={
            'username': self.user.username,
            'id_string': id_string
        })
        # save current user before we re-assign
        bob = self.user
        self._create_user_and_login('alice', 'alice')
        self.client.post(xform_delete_url)
        form_deleted = XForm.objects.filter(user=bob,
            id_string = id_string).count() == 0
        self.assertFalse(form_deleted)

    def test_xform_delete_cascades_mongo_instances(self):
        initial_mongo_count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]["count"]
        # submit instance
        for i in range(len(self.surveys)):
            self._submit_transport_instance(i)
        # check mongo record exists
        mongo_count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]["count"]
        self.assertEqual(mongo_count, initial_mongo_count + len(self.surveys))
        # delete form
        xform_delete_url = reverse(delete_xform, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })
        self.client.post(xform_delete_url)
        mongo_count = ParsedInstance.query_mongo(
            self.user.username, self.xform.id_string, '{}', '[]', '{}',
            count=True)[0]["count"]
        self.assertEqual(mongo_count, initial_mongo_count)
