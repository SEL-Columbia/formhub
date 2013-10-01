import os

from xml.dom import minidom, Node
from django.conf import settings

from api.tests.test_api import TestAPICase
from api.views import XFormViewSet


class TestFormsAPI(TestAPICase):
    def setUp(self):
        super(TestFormsAPI, self).setUp()
        self.view = XFormViewSet.as_view({
            'get': 'list',
        })

    def test_form_list(self):
        self._publish_xls_form_to_project()
        request = self.factory.get('/', **self.extra)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [self.form_data])

    def test_form_get(self):
        self._publish_xls_form_to_project()
        view = XFormViewSet.as_view({
            'get': 'retrieve'
        })
        request = self.factory.get('/', **self.extra)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'detail': 'Expected URL keyword argument `owner`.'})
        request = self.factory.get('/', **self.extra)
        response = view(request, owner='bob', pk=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.form_data)

    def test_form_format(self):
        self._publish_xls_form_to_project()
        view = XFormViewSet.as_view({
            'get': 'form'
        })
        data = {
            "name": "transportation",
            "title": "transportation_2011_07_25",
            "default_language": "default",
            "id_string": "transportation_2011_07_25",
            "type": "survey",
        }
        request = self.factory.get('/', **self.extra)
        response = view(request, owner='bob', pk=1, formid=1, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset(data, response.data)
        response = view(request, owner='bob', pk=1, formid=1, format='xml')
        self.assertEqual(response.status_code, 200)
        response_doc = minidom.parseString(response.data)

        xml_path = os.path.join(
            settings.PROJECT_ROOT, "main", "tests", "fixtures",
            "transportation", "transportation.xml")
        with open(xml_path) as xml_file:
            expected_doc = minidom.parse(xml_file)

        model_node = [
            n for n in
            response_doc.getElementsByTagName("h:head")[0].childNodes
            if n.nodeType == Node.ELEMENT_NODE and
            n.tagName == "model"][0]

        # check for UUID and remove
        uuid_nodes = [
            node for node in model_node.childNodes
            if node.nodeType == Node.ELEMENT_NODE
            and node.getAttribute("nodeset") == "/transportation/formhub/uuid"]
        self.assertEqual(len(uuid_nodes), 1)
        uuid_node = uuid_nodes[0]
        uuid_node.setAttribute("calculate", "''")

        # check content without UUID
        self.assertEqual(response_doc.toxml(), expected_doc.toxml())

    def test_form_tags(self):
        self._publish_xls_form_to_project()
        view = XFormViewSet.as_view({
            'get': 'labels',
            'post': 'labels',
            'delete': 'labels'
        })
        # no tags
        request = self.factory.get('/', **self.extra)
        response = view(request, owner='bob', pk=1, formid=1)
        self.assertEqual(response.data, [])
        # add tag "hello"
        request = self.factory.post('/', data={"tags": "hello"}, **self.extra)
        response = view(request, owner='bob', pk=1, formid=1)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, [u'hello'])
        # remove tag "hello"
        request = self.factory.delete('/', data={"tags": "hello"},
                                      **self.extra)
        response = view(request, owner='bob', pk=1, formid=1, label='hello')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
