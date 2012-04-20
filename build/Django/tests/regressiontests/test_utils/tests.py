import sys

from django.test import TestCase, skipUnlessDBFeature, skipIfDBFeature

from models import Person

if sys.version_info >= (2, 5):
    from tests_25 import AssertNumQueriesContextManagerTests


class SkippingTestCase(TestCase):
    def test_skip_unless_db_feature(self):
        "A test that might be skipped is actually called."
        # Total hack, but it works, just want an attribute that's always true.
        @skipUnlessDBFeature("__class__")
        def test_func():
            raise ValueError

        self.assertRaises(ValueError, test_func)


class AssertNumQueriesTests(TestCase):
    def test_assert_num_queries(self):
        def test_func():
            raise ValueError

        self.assertRaises(ValueError,
            self.assertNumQueries, 2, test_func
        )

    def test_assert_num_queries_with_client(self):
        person = Person.objects.create(name='test')

        self.assertNumQueries(
            1,
            self.client.get,
            "/test_utils/get_person/%s/" % person.pk
        )

        self.assertNumQueries(
            1,
            self.client.get,
            "/test_utils/get_person/%s/" % person.pk
        )

        def test_func():
            self.client.get("/test_utils/get_person/%s/" % person.pk)
            self.client.get("/test_utils/get_person/%s/" % person.pk)
        self.assertNumQueries(2, test_func)


class SaveRestoreWarningState(TestCase):
    def test_save_restore_warnings_state(self):
        """
        Ensure save_warnings_state/restore_warnings_state work correctly.
        """
        # In reality this test could be satisfied by many broken implementations
        # of save_warnings_state/restore_warnings_state (e.g. just
        # warnings.resetwarnings()) , but it is difficult to test more.
        import warnings
        self.save_warnings_state()

        class MyWarning(Warning):
            pass

        # Add a filter that causes an exception to be thrown, so we can catch it
        warnings.simplefilter("error", MyWarning)
        self.assertRaises(Warning, lambda: warnings.warn("warn", MyWarning))

        # Now restore.
        self.restore_warnings_state()
        # After restoring, we shouldn't get an exception. But we don't want a
        # warning printed either, so we have to silence the warning.
        warnings.simplefilter("ignore", MyWarning)
        warnings.warn("warn", MyWarning)

        # Remove the filter we just added.
        self.restore_warnings_state()

__test__ = {"API_TEST": r"""
# Some checks of the doctest output normalizer.
# Standard doctests do fairly
>>> from django.utils import simplejson
>>> from django.utils.xmlutils import SimplerXMLGenerator
>>> from StringIO import StringIO

>>> def produce_long():
...     return 42L

>>> def produce_int():
...     return 42

>>> def produce_json():
...     return simplejson.dumps(['foo', {'bar': ('baz', None, 1.0, 2), 'whiz': 42}])

>>> def produce_xml():
...     stream = StringIO()
...     xml = SimplerXMLGenerator(stream, encoding='utf-8')
...     xml.startDocument()
...     xml.startElement("foo", {"aaa" : "1.0", "bbb": "2.0"})
...     xml.startElement("bar", {"ccc" : "3.0"})
...     xml.characters("Hello")
...     xml.endElement("bar")
...     xml.startElement("whiz", {})
...     xml.characters("Goodbye")
...     xml.endElement("whiz")
...     xml.endElement("foo")
...     xml.endDocument()
...     return stream.getvalue()

>>> def produce_xml_fragment():
...     stream = StringIO()
...     xml = SimplerXMLGenerator(stream, encoding='utf-8')
...     xml.startElement("foo", {"aaa": "1.0", "bbb": "2.0"})
...     xml.characters("Hello")
...     xml.endElement("foo")
...     xml.startElement("bar", {"ccc": "3.0", "ddd": "4.0"})
...     xml.endElement("bar")
...     return stream.getvalue()

# Long values are normalized and are comparable to normal integers ...
>>> produce_long()
42

# ... and vice versa
>>> produce_int()
42L

# JSON output is normalized for field order, so it doesn't matter
# which order json dictionary attributes are listed in output
>>> produce_json()
'["foo", {"bar": ["baz", null, 1.0, 2], "whiz": 42}]'

>>> produce_json()
'["foo", {"whiz": 42, "bar": ["baz", null, 1.0, 2]}]'

# XML output is normalized for attribute order, so it doesn't matter
# which order XML element attributes are listed in output
>>> produce_xml()
'<?xml version="1.0" encoding="UTF-8"?>\n<foo aaa="1.0" bbb="2.0"><bar ccc="3.0">Hello</bar><whiz>Goodbye</whiz></foo>'

>>> produce_xml()
'<?xml version="1.0" encoding="UTF-8"?>\n<foo bbb="2.0" aaa="1.0"><bar ccc="3.0">Hello</bar><whiz>Goodbye</whiz></foo>'

>>> produce_xml_fragment()
'<foo aaa="1.0" bbb="2.0">Hello</foo><bar ccc="3.0" ddd="4.0"></bar>'

>>> produce_xml_fragment()
'<foo bbb="2.0" aaa="1.0">Hello</foo><bar ddd="4.0" ccc="3.0"></bar>'

"""}
