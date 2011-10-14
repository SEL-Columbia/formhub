import os
from django.test import TestCase
from main.views import GoogleDoc


class TestGoogleDoc(TestCase):

    def test_view(self):
        doc = GoogleDoc()
        folder = os.path.join(
            os.path.dirname(__file__), "fixtures", "google_doc"
            )
        input_path = os.path.join(folder, "input.html")
        with open(input_path) as f:
            input_html = f.read()
        doc.set_html(input_html)
        self.assertEqual(doc._html, input_html)
        self.assertEqual(len(doc._sections), 14)
        output_path = os.path.join(folder, "navigation.html")
        with open(output_path) as f:
            self.assertEquals(doc._navigation_html(), f.read())
