from django.core.urlresolvers import reverse

from main.tests.test_base import MainTestCase
from odk_viewer.views import chart
from guardian.shortcuts import assign, remove_perm


class TestChartView(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form_and_submit_instance()
        self.url = reverse(chart, kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string
        })


    def test_chart_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_restrict_for_anon(self):
        response = self.anon.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_restrict_for_shared(self):
        self.xform.shared_data=True
        self.xform.save()
        response =self.anon.get(self.url)
        self.assertEqual(response.status_code, 200)
