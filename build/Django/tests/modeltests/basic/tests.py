from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import models, DEFAULT_DB_ALIAS, connection
from django.db.models.fields import FieldDoesNotExist
from django.test import TestCase, skipIfDBFeature, skipUnlessDBFeature

from models import Article


class ModelTest(TestCase):

    def test_lookup(self):
        # No articles are in the system yet.
        self.assertQuerysetEqual(Article.objects.all(), [])

        # Create an Article.
        a = Article(
            id=None,
            headline='Area man programs in Python',
            pub_date=datetime(2005, 7, 28),
        )

        # Save it into the database. You have to call save() explicitly.
        a.save()

        # Now it has an ID.
        self.assertTrue(a.id != None)

        # Models have a pk property that is an alias for the primary key
        # attribute (by default, the 'id' attribute).
        self.assertEqual(a.pk, a.id)

        # Access database columns via Python attributes.
        self.assertEqual(a.headline, 'Area man programs in Python')
        self.assertEqual(a.pub_date, datetime(2005, 7, 28, 0, 0))

        # Change values by changing the attributes, then calling save().
        a.headline = 'Area woman programs in Python'
        a.save()

        # Article.objects.all() returns all the articles in the database.
        self.assertQuerysetEqual(Article.objects.all(),
            ['<Article: Area woman programs in Python>'])

        # Django provides a rich database lookup API.
        self.assertEqual(Article.objects.get(id__exact=a.id), a)
        self.assertEqual(Article.objects.get(headline__startswith='Area woman'), a)
        self.assertEqual(Article.objects.get(pub_date__year=2005), a)
        self.assertEqual(Article.objects.get(pub_date__year=2005, pub_date__month=7), a)
        self.assertEqual(Article.objects.get(pub_date__year=2005, pub_date__month=7, pub_date__day=28), a)
        self.assertEqual(Article.objects.get(pub_date__week_day=5), a)

        # The "__exact" lookup type can be omitted, as a shortcut.
        self.assertEqual(Article.objects.get(id=a.id), a)
        self.assertEqual(Article.objects.get(headline='Area woman programs in Python'), a)

        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__year=2005),
            ['<Article: Area woman programs in Python>'],
        )
        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__year=2004),
            [],
        )
        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__year=2005, pub_date__month=7),
            ['<Article: Area woman programs in Python>'],
        )

        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__week_day=5),
            ['<Article: Area woman programs in Python>'],
        )
        self.assertQuerysetEqual(
            Article.objects.filter(pub_date__week_day=6),
            [],
        )

        # Django raises an Article.DoesNotExist exception for get() if the
        # parameters don't match any object.
        self.assertRaisesRegexp(
            ObjectDoesNotExist,
            "Article matching query does not exist.",
            Article.objects.get,
            id__exact=2000,
        )

        self.assertRaisesRegexp(
            ObjectDoesNotExist,
            "Article matching query does not exist.",
            Article.objects.get,
            pub_date__year=2005,
            pub_date__month=8,
        )

        self.assertRaisesRegexp(
            ObjectDoesNotExist,
            "Article matching query does not exist.",
            Article.objects.get,
            pub_date__week_day=6,
        )

        # Lookup by a primary key is the most common case, so Django
        # provides a shortcut for primary-key exact lookups.
        # The following is identical to articles.get(id=a.id).
        self.assertEqual(Article.objects.get(pk=a.id), a)

        # pk can be used as a shortcut for the primary key name in any query.
        self.assertQuerysetEqual(Article.objects.filter(pk__in=[a.id]),
            ["<Article: Area woman programs in Python>"])

        # Model instances of the same type and same ID are considered equal.
        a = Article.objects.get(pk=a.id)
        b = Article.objects.get(pk=a.id)
        self.assertEqual(a, b)

    def test_object_creation(self):
        # Create an Article.
        a = Article(
            id=None,
            headline='Area man programs in Python',
            pub_date=datetime(2005, 7, 28),
        )

        # Save it into the database. You have to call save() explicitly.
        a.save()

        # You can initialize a model instance using positional arguments,
        # which should match the field order as defined in the model.
        a2 = Article(None, 'Second article', datetime(2005, 7, 29))
        a2.save()

        self.assertNotEqual(a2.id, a.id)
        self.assertEqual(a2.headline, 'Second article')
        self.assertEqual(a2.pub_date, datetime(2005, 7, 29, 0, 0))

        # ...or, you can use keyword arguments.
        a3 = Article(
            id=None,
            headline='Third article',
            pub_date=datetime(2005, 7, 30),
        )
        a3.save()

        self.assertNotEqual(a3.id, a.id)
        self.assertNotEqual(a3.id, a2.id)
        self.assertEqual(a3.headline, 'Third article')
        self.assertEqual(a3.pub_date, datetime(2005, 7, 30, 0, 0))

        # You can also mix and match position and keyword arguments, but
        # be sure not to duplicate field information.
        a4 = Article(None, 'Fourth article', pub_date=datetime(2005, 7, 31))
        a4.save()
        self.assertEqual(a4.headline, 'Fourth article')

        # Don't use invalid keyword arguments.
        self.assertRaisesRegexp(
            TypeError,
            "'foo' is an invalid keyword argument for this function",
            Article,
            id=None,
            headline='Invalid',
            pub_date=datetime(2005, 7, 31),
            foo='bar',
        )

        # You can leave off the value for an AutoField when creating an
        # object, because it'll get filled in automatically when you save().
        a5 = Article(headline='Article 6', pub_date=datetime(2005, 7, 31))
        a5.save()
        self.assertEqual(a5.headline, 'Article 6')

        # If you leave off a field with "default" set, Django will use
        # the default.
        a6 = Article(pub_date=datetime(2005, 7, 31))
        a6.save()
        self.assertEqual(a6.headline, u'Default headline')

        # For DateTimeFields, Django saves as much precision (in seconds)
        # as you give it.
        a7 = Article(
            headline='Article 7',
            pub_date=datetime(2005, 7, 31, 12, 30),
        )
        a7.save()
        self.assertEqual(Article.objects.get(id__exact=a7.id).pub_date,
            datetime(2005, 7, 31, 12, 30))

        a8 = Article(
            headline='Article 8',
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a8.save()
        self.assertEqual(Article.objects.get(id__exact=a8.id).pub_date,
            datetime(2005, 7, 31, 12, 30, 45))

        # Saving an object again doesn't create a new object -- it just saves
        # the old one.
        current_id = a8.id
        a8.save()
        self.assertEqual(a8.id, current_id)
        a8.headline = 'Updated article 8'
        a8.save()
        self.assertEqual(a8.id, current_id)

        # Check that != and == operators behave as expecte on instances
        self.assertTrue(a7 != a8)
        self.assertFalse(a7 == a8)
        self.assertEqual(a8, Article.objects.get(id__exact=a8.id))

        self.assertTrue(Article.objects.get(id__exact=a8.id) != Article.objects.get(id__exact=a7.id))
        self.assertFalse(Article.objects.get(id__exact=a8.id) == Article.objects.get(id__exact=a7.id))

        # You can use 'in' to test for membership...
        self.assertTrue(a8 in Article.objects.all())

        # ... but there will often be more efficient ways if that is all you need:
        self.assertTrue(Article.objects.filter(id=a8.id).exists())

        # dates() returns a list of available dates of the given scope for
        # the given field.
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'year'),
            ["datetime.datetime(2005, 1, 1, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'month'),
            ["datetime.datetime(2005, 7, 1, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'day'),
            ["datetime.datetime(2005, 7, 28, 0, 0)",
             "datetime.datetime(2005, 7, 29, 0, 0)",
             "datetime.datetime(2005, 7, 30, 0, 0)",
             "datetime.datetime(2005, 7, 31, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'day', order='ASC'),
            ["datetime.datetime(2005, 7, 28, 0, 0)",
             "datetime.datetime(2005, 7, 29, 0, 0)",
             "datetime.datetime(2005, 7, 30, 0, 0)",
             "datetime.datetime(2005, 7, 31, 0, 0)"])
        self.assertQuerysetEqual(
            Article.objects.dates('pub_date', 'day', order='DESC'),
            ["datetime.datetime(2005, 7, 31, 0, 0)",
             "datetime.datetime(2005, 7, 30, 0, 0)",
             "datetime.datetime(2005, 7, 29, 0, 0)",
             "datetime.datetime(2005, 7, 28, 0, 0)"])

        # dates() requires valid arguments.
        self.assertRaisesRegexp(
            TypeError,
            "dates\(\) takes at least 3 arguments \(1 given\)",
            Article.objects.dates,
        )

        self.assertRaisesRegexp(
            FieldDoesNotExist,
            "Article has no field named 'invalid_field'",
            Article.objects.dates,
            "invalid_field",
            "year",
        )

        self.assertRaisesRegexp(
            AssertionError,
            "'kind' must be one of 'year', 'month' or 'day'.",
            Article.objects.dates,
            "pub_date",
            "bad_kind",
        )

        self.assertRaisesRegexp(
            AssertionError,
            "'order' must be either 'ASC' or 'DESC'.",
            Article.objects.dates,
            "pub_date",
            "year",
            order="bad order",
        )

        # Use iterator() with dates() to return a generator that lazily
        # requests each result one at a time, to save memory.
        dates = []
        for article in Article.objects.dates('pub_date', 'day', order='DESC').iterator():
            dates.append(article)
        self.assertEqual(dates, [
            datetime(2005, 7, 31, 0, 0),
            datetime(2005, 7, 30, 0, 0),
            datetime(2005, 7, 29, 0, 0),
            datetime(2005, 7, 28, 0, 0)])

        # You can combine queries with & and |.
        s1 = Article.objects.filter(id__exact=a.id)
        s2 = Article.objects.filter(id__exact=a2.id)
        self.assertQuerysetEqual(s1 | s2,
            ["<Article: Area man programs in Python>",
             "<Article: Second article>"])
        self.assertQuerysetEqual(s1 & s2, [])

        # You can get the number of objects like this:
        self.assertEqual(len(Article.objects.filter(id__exact=a.id)), 1)

        # You can get items using index and slice notation.
        self.assertEqual(Article.objects.all()[0], a)
        self.assertQuerysetEqual(Article.objects.all()[1:3],
            ["<Article: Second article>", "<Article: Third article>"])

        s3 = Article.objects.filter(id__exact=a3.id)
        self.assertQuerysetEqual((s1 | s2 | s3)[::2],
            ["<Article: Area man programs in Python>",
             "<Article: Third article>"])

        # Slicing works with longs.
        self.assertEqual(Article.objects.all()[0L], a)
        self.assertQuerysetEqual(Article.objects.all()[1L:3L],
            ["<Article: Second article>", "<Article: Third article>"])
        self.assertQuerysetEqual((s1 | s2 | s3)[::2L],
            ["<Article: Area man programs in Python>",
             "<Article: Third article>"])

        # And can be mixed with ints.
        self.assertQuerysetEqual(Article.objects.all()[1:3L],
            ["<Article: Second article>", "<Article: Third article>"])

        # Slices (without step) are lazy:
        self.assertQuerysetEqual(Article.objects.all()[0:5].filter(),
            ["<Article: Area man programs in Python>",
             "<Article: Second article>",
             "<Article: Third article>",
             "<Article: Article 6>",
             "<Article: Default headline>"])

        # Slicing again works:
        self.assertQuerysetEqual(Article.objects.all()[0:5][0:2],
            ["<Article: Area man programs in Python>",
             "<Article: Second article>"])
        self.assertQuerysetEqual(Article.objects.all()[0:5][:2],
            ["<Article: Area man programs in Python>",
             "<Article: Second article>"])
        self.assertQuerysetEqual(Article.objects.all()[0:5][4:],
            ["<Article: Default headline>"])
        self.assertQuerysetEqual(Article.objects.all()[0:5][5:], [])

        # Some more tests!
        self.assertQuerysetEqual(Article.objects.all()[2:][0:2],
            ["<Article: Third article>", "<Article: Article 6>"])
        self.assertQuerysetEqual(Article.objects.all()[2:][:2],
            ["<Article: Third article>", "<Article: Article 6>"])
        self.assertQuerysetEqual(Article.objects.all()[2:][2:3],
            ["<Article: Default headline>"])

        # Using an offset without a limit is also possible.
        self.assertQuerysetEqual(Article.objects.all()[5:],
            ["<Article: Fourth article>",
             "<Article: Article 7>",
             "<Article: Updated article 8>"])

        # Also, once you have sliced you can't filter, re-order or combine
        self.assertRaisesRegexp(
            AssertionError,
            "Cannot filter a query once a slice has been taken.",
            Article.objects.all()[0:5].filter,
            id=a.id,
        )

        self.assertRaisesRegexp(
            AssertionError,
            "Cannot reorder a query once a slice has been taken.",
            Article.objects.all()[0:5].order_by,
            'id',
        )

        try:
            Article.objects.all()[0:1] & Article.objects.all()[4:5]
            self.fail('Should raise an AssertionError')
        except AssertionError, e:
            self.assertEqual(str(e), "Cannot combine queries once a slice has been taken.")
        except Exception, e:
            self.fail('Should raise an AssertionError, not %s' % e)

        # Negative slices are not supported, due to database constraints.
        # (hint: inverting your ordering might do what you need).
        try:
            Article.objects.all()[-1]
            self.fail('Should raise an AssertionError')
        except AssertionError, e:
            self.assertEqual(str(e), "Negative indexing is not supported.")
        except Exception, e:
            self.fail('Should raise an AssertionError, not %s' % e)

        error = None
        try:
            Article.objects.all()[0:-5]
        except Exception, e:
            error = e
        self.assertTrue(isinstance(error, AssertionError))
        self.assertEqual(str(error), "Negative indexing is not supported.")

        # An Article instance doesn't have access to the "objects" attribute.
        # That's only available on the class.
        self.assertRaisesRegexp(
            AttributeError,
            "Manager isn't accessible via Article instances",
            getattr,
            a7,
            "objects",
        )

        # Bulk delete test: How many objects before and after the delete?
        self.assertQuerysetEqual(Article.objects.all(),
            ["<Article: Area man programs in Python>",
             "<Article: Second article>",
             "<Article: Third article>",
             "<Article: Article 6>",
             "<Article: Default headline>",
             "<Article: Fourth article>",
             "<Article: Article 7>",
             "<Article: Updated article 8>"])
        Article.objects.filter(id__lte=a4.id).delete()
        self.assertQuerysetEqual(Article.objects.all(),
            ["<Article: Article 6>",
             "<Article: Default headline>",
             "<Article: Article 7>",
             "<Article: Updated article 8>"])

    @skipUnlessDBFeature('supports_microsecond_precision')
    def test_microsecond_precision(self):
        # In PostgreSQL, microsecond-level precision is available.
        a9 = Article(
            headline='Article 9',
            pub_date=datetime(2005, 7, 31, 12, 30, 45, 180),
        )
        a9.save()
        self.assertEqual(Article.objects.get(pk=a9.pk).pub_date,
            datetime(2005, 7, 31, 12, 30, 45, 180))

    @skipIfDBFeature('supports_microsecond_precision')
    def test_microsecond_precision_not_supported(self):
        # In MySQL, microsecond-level precision isn't available. You'll lose
        # microsecond-level precision once the data is saved.
        a9 = Article(
            headline='Article 9',
            pub_date=datetime(2005, 7, 31, 12, 30, 45, 180),
        )
        a9.save()
        self.assertEqual(Article.objects.get(id__exact=a9.id).pub_date,
            datetime(2005, 7, 31, 12, 30, 45))

    def test_manually_specify_primary_key(self):
        # You can manually specify the primary key when creating a new object.
        a101 = Article(
            id=101,
            headline='Article 101',
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a101.save()
        a101 = Article.objects.get(pk=101)
        self.assertEqual(a101.headline, u'Article 101')

    def test_create_method(self):
        # You can create saved objects in a single step
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        self.assertEqual(Article.objects.get(headline="Article 10"), a10)

    def test_year_lookup_edge_case(self):
        # Edge-case test: A year lookup should retrieve all objects in
        # the given year, including Jan. 1 and Dec. 31.
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )
        self.assertQuerysetEqual(Article.objects.filter(pub_date__year=2008),
            ["<Article: Article 11>", "<Article: Article 12>"])

    def test_unicode_data(self):
        # Unicode data works, too.
        a = Article(
            headline=u'\u6797\u539f \u3081\u3050\u307f',
            pub_date=datetime(2005, 7, 28),
        )
        a.save()
        self.assertEqual(Article.objects.get(pk=a.id).headline,
            u'\u6797\u539f \u3081\u3050\u307f')

    def test_hash_function(self):
        # Model instances have a hash function, so they can be used in sets
        # or as dictionary keys. Two models compare as equal if their primary
        # keys are equal.
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )

        s = set([a10, a11, a12])
        self.assertTrue(Article.objects.get(headline='Article 11') in s)

    def test_extra_method_select_argument_with_dashes_and_values(self):
        # The 'select' argument to extra() supports names with dashes in
        # them, as long as you use values().
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )

        dicts = Article.objects.filter(
            pub_date__year=2008).extra(
                select={'dashed-value': '1'}
            ).values('headline', 'dashed-value')
        self.assertEqual([sorted(d.items()) for d in dicts],
            [[('dashed-value', 1), ('headline', u'Article 11')], [('dashed-value', 1), ('headline', u'Article 12')]])

    def test_extra_method_select_argument_with_dashes(self):
        # If you use 'select' with extra() and names containing dashes on a
        # query that's *not* a values() query, those extra 'select' values
        # will silently be ignored.
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a11 = Article.objects.create(
            headline='Article 11',
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline='Article 12',
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )

        articles = Article.objects.filter(
            pub_date__year=2008).extra(
                select={'dashed-value': '1', 'undashedvalue': '2'})
        self.assertEqual(articles[0].undashedvalue, 2)
