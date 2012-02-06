from test_base import MainTestCase
from test_process import TestSite
from main.views import clone
from odk_logger.models import XForm

class TestFormGallery(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transporation_form()
        self.url = reverse(clone, kwargs={'username': self.user.username,
                'id_string': self.xform.id_string})

    def test_require_use_is_auth(self):
        count = XForm.objects.all()
        self.anon.post(self.url)
        self.assertEqual(count, XForm.objects.all())

    def test_clone_for_other_user(self):
        self.create_use_and_login('alice', 'alice')
        count = XForm.objects.all()
        self.user.post(self.url)
        self.assertEqual(count + 1, XForm.objects.all())

