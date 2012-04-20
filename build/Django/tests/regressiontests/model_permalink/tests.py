from django.test import TestCase
from regressiontests.model_permalink.models import Guitarist

class PermalinkTests(TestCase):
    urls = 'regressiontests.model_permalink.urls'

    def test_permalink(self):
        g = Guitarist(name='Adrien Moignard', slug='adrienmoignard')
        self.assertEqual(g.url(), '/guitarists/adrienmoignard/')

    def test_wrapped_docstring(self):
        "Methods using the @permalink decorator retain their docstring."
        g = Guitarist(name='Adrien Moignard', slug='adrienmoignard')
        self.assertEqual(g.url.__doc__, "Returns the URL for this guitarist.")
