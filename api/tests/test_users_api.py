import json
from api.tests.test_api import TestAPICase
from api.views import UserViewSet


class TestUsersAPI(TestAPICase):
    def setUp(self):
        super(TestUsersAPI, self).setUp()

    def test_user_list(self):
        view = UserViewSet.as_view({'get': 'list'})
        request = self.factory.get('/', **self.extra)
        response = view(request)
        data = [{'username': u'bob', 'first_name': u'Bob', 'last_name': u''}]
        self.assertContains(response, json.dumps(data))

    def test_user_get(self):
        view = UserViewSet.as_view({'get': 'retrieve'})
        request = self.factory.get('/', **self.extra)
        response = view(request, username='bob')
        data = {'username': u'bob', 'first_name': u'Bob', 'last_name': u''}
        self.assertContains(response, json.dumps(data))
