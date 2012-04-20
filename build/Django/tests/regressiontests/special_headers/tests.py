from django.test import TestCase
from django.contrib.auth.models import User

class SpecialHeadersTest(TestCase):
    fixtures = ['data.xml']

    def test_xheaders(self):
        user = User.objects.get(username='super')
        response = self.client.get('/special_headers/article/1/')
        # import pdb; pdb.set_trace()
        self.assertFalse('X-Object-Type' in response)
        self.client.login(username='super', password='secret')
        response = self.client.get('/special_headers/article/1/')
        self.assertTrue('X-Object-Type' in response)
        user.is_staff = False
        user.save()
        response = self.client.get('/special_headers/article/1/')
        self.assertFalse('X-Object-Type' in response)
        user.is_staff = True
        user.is_active = False
        user.save()
        response = self.client.get('/special_headers/article/1/')
        self.assertFalse('X-Object-Type' in response)

    def test_xview_func(self):
        user = User.objects.get(username='super')
        response = self.client.head('/special_headers/xview/func/')
        self.assertFalse('X-View' in response)
        self.client.login(username='super', password='secret')
        response = self.client.head('/special_headers/xview/func/')
        self.assertTrue('X-View' in response)
        self.assertEqual(response['X-View'], 'regressiontests.special_headers.views.xview')
        user.is_staff = False
        user.save()
        response = self.client.head('/special_headers/xview/func/')
        self.assertFalse('X-View' in response)
        user.is_staff = True
        user.is_active = False
        user.save()
        response = self.client.head('/special_headers/xview/func/')
        self.assertFalse('X-View' in response)

    def test_xview_class(self):
        user = User.objects.get(username='super')
        response = self.client.head('/special_headers/xview/class/')
        self.assertFalse('X-View' in response)
        self.client.login(username='super', password='secret')
        response = self.client.head('/special_headers/xview/class/')
        self.assertTrue('X-View' in response)
        self.assertEqual(response['X-View'], 'regressiontests.special_headers.views.XViewClass')
        user.is_staff = False
        user.save()
        response = self.client.head('/special_headers/xview/class/')
        self.assertFalse('X-View' in response)
        user.is_staff = True
        user.is_active = False
        user.save()
        response = self.client.head('/special_headers/xview/class/')
        self.assertFalse('X-View' in response)
