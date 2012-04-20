from datetime import datetime
from django.test import TestCase
from django.core.exceptions import FieldError
from models import Article, Reporter

class ManyToOneTests(TestCase):

    def setUp(self):
        # Create a few Reporters.
        self.r = Reporter(first_name='John', last_name='Smith', email='john@example.com')
        self.r.save()
        self.r2 = Reporter(first_name='Paul', last_name='Jones', email='paul@example.com')
        self.r2.save()
        # Create an Article.
        self.a = Article(id=None, headline="This is a test",
                         pub_date=datetime(2005, 7, 27), reporter=self.r)
        self.a.save()

    def test_get(self):
        # Article objects have access to their related Reporter objects.
        r = self.a.reporter
        self.assertEqual(r.id, self.r.id)
        # These are strings instead of unicode strings because that's what was used in
        # the creation of this reporter (and we haven't refreshed the data from the
        # database, which always returns unicode strings).
        self.assertEqual((r.first_name, self.r.last_name), ('John', 'Smith'))

    def test_create(self):
        # You can also instantiate an Article by passing the Reporter's ID
        # instead of a Reporter object.
        a3 = Article(id=None, headline="Third article",
                     pub_date=datetime(2005, 7, 27), reporter_id=self.r.id)
        a3.save()
        self.assertEqual(a3.reporter.id, self.r.id)

        # Similarly, the reporter ID can be a string.
        a4 = Article(id=None, headline="Fourth article",
                     pub_date=datetime(2005, 7, 27), reporter_id=str(self.r.id))
        a4.save()
        self.assertEqual(repr(a4.reporter), "<Reporter: John Smith>")

    def test_add(self):
        # Create an Article via the Reporter object.
        new_article = self.r.article_set.create(headline="John's second story",
                                                pub_date=datetime(2005, 7, 29))
        self.assertEqual(repr(new_article), "<Article: John's second story>")
        self.assertEqual(new_article.reporter.id, self.r.id)

        # Create a new article, and add it to the article set.
        new_article2 = Article(headline="Paul's story", pub_date=datetime(2006, 1, 17))
        self.r.article_set.add(new_article2)
        self.assertEqual(new_article2.reporter.id, self.r.id)
        self.assertQuerysetEqual(self.r.article_set.all(),
            [
                "<Article: John's second story>",
                "<Article: Paul's story>",
                "<Article: This is a test>",
            ])

        # Add the same article to a different article set - check that it moves.
        self.r2.article_set.add(new_article2)
        self.assertEqual(new_article2.reporter.id, self.r2.id)
        self.assertQuerysetEqual(self.r2.article_set.all(), ["<Article: Paul's story>"])

        # Adding an object of the wrong type raises TypeError.
        self.assertRaises(TypeError, self.r.article_set.add, self.r2)
        self.assertQuerysetEqual(self.r.article_set.all(),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])

    def test_assign(self):
        new_article = self.r.article_set.create(headline="John's second story",
                                                pub_date=datetime(2005, 7, 29))
        new_article2 = self.r2.article_set.create(headline="Paul's story",
                                                  pub_date=datetime(2006, 1, 17))
        # Assign the article to the reporter directly using the descriptor.
        new_article2.reporter = self.r
        new_article2.save()
        self.assertEqual(repr(new_article2.reporter), "<Reporter: John Smith>")
        self.assertEqual(new_article2.reporter.id, self.r.id)
        self.assertQuerysetEqual(self.r.article_set.all(), [
            "<Article: John's second story>",
            "<Article: Paul's story>",
            "<Article: This is a test>",
        ])
        self.assertQuerysetEqual(self.r2.article_set.all(), [])
        # Set the article back again using set descriptor.
        self.r2.article_set = [new_article, new_article2]
        self.assertQuerysetEqual(self.r.article_set.all(), ["<Article: This is a test>"])
        self.assertQuerysetEqual(self.r2.article_set.all(),
            [
                "<Article: John's second story>",
                "<Article: Paul's story>",
            ])

        # Funny case - assignment notation can only go so far; because the
        # ForeignKey cannot be null, existing members of the set must remain.
        self.r.article_set = [new_article]
        self.assertQuerysetEqual(self.r.article_set.all(),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(self.r2.article_set.all(), ["<Article: Paul's story>"])
        # Reporter cannot be null - there should not be a clear or remove method
        self.assertFalse(hasattr(self.r2.article_set, 'remove'))
        self.assertFalse(hasattr(self.r2.article_set, 'clear'))

    def test_selects(self):
        new_article = self.r.article_set.create(headline="John's second story",
                                                pub_date=datetime(2005, 7, 29))
        new_article2 = self.r2.article_set.create(headline="Paul's story",
                                                  pub_date=datetime(2006, 1, 17))
        # Reporter objects have access to their related Article objects.
        self.assertQuerysetEqual(self.r.article_set.all(), [
            "<Article: John's second story>",
            "<Article: This is a test>",
        ])
        self.assertQuerysetEqual(self.r.article_set.filter(headline__startswith='This'),
                                 ["<Article: This is a test>"])
        self.assertEqual(self.r.article_set.count(), 2)
        self.assertEqual(self.r2.article_set.count(), 1)
        # Get articles by id
        self.assertQuerysetEqual(Article.objects.filter(id__exact=self.a.id),
                                 ["<Article: This is a test>"])
        self.assertQuerysetEqual(Article.objects.filter(pk=self.a.id),
                                 ["<Article: This is a test>"])
        # Query on an article property
        self.assertQuerysetEqual(Article.objects.filter(headline__startswith='This'),
                                 ["<Article: This is a test>"])
        # The API automatically follows relationships as far as you need.
        # Use double underscores to separate relationships.
        # This works as many levels deep as you want. There's no limit.
        # Find all Articles for any Reporter whose first name is "John".
        self.assertQuerysetEqual(Article.objects.filter(reporter__first_name__exact='John'),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        # Check that implied __exact also works
        self.assertQuerysetEqual(Article.objects.filter(reporter__first_name='John'),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        # Query twice over the related field.
        self.assertQuerysetEqual(
            Article.objects.filter(reporter__first_name__exact='John',
                                   reporter__last_name__exact='Smith'),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        # The underlying query only makes one join when a related table is referenced twice.
        queryset = Article.objects.filter(reporter__first_name__exact='John',
                                       reporter__last_name__exact='Smith')
        self.assertNumQueries(1, list, queryset)
        self.assertEqual(queryset.query.get_compiler(queryset.db).as_sql()[0].count('INNER JOIN'), 1)

        # The automatically joined table has a predictable name.
        self.assertQuerysetEqual(
            Article.objects.filter(reporter__first_name__exact='John').extra(
                where=["many_to_one_reporter.last_name='Smith'"]),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        # ... and should work fine with the unicode that comes out of forms.Form.cleaned_data
        self.assertQuerysetEqual(
            Article.objects.filter(reporter__first_name__exact='John'
                                  ).extra(where=["many_to_one_reporter.last_name='%s'" % u'Smith']),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        # Find all Articles for a Reporter.
        # Use direct ID check, pk check, and object comparison
        self.assertQuerysetEqual(
            Article.objects.filter(reporter__id__exact=self.r.id),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(
            Article.objects.filter(reporter__pk=self.r.id),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(
            Article.objects.filter(reporter=self.r.id),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(
            Article.objects.filter(reporter=self.r),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(
            Article.objects.filter(reporter__in=[self.r.id,self.r2.id]).distinct(),
            [
                    "<Article: John's second story>",
                    "<Article: Paul's story>",
                    "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(
            Article.objects.filter(reporter__in=[self.r,self.r2]).distinct(),
            [
                "<Article: John's second story>",
                "<Article: Paul's story>",
                "<Article: This is a test>",
            ])
        # You can also use a queryset instead of a literal list of instances.
        # The queryset must be reduced to a list of values using values(),
        # then converted into a query
        self.assertQuerysetEqual(
            Article.objects.filter(
                        reporter__in=Reporter.objects.filter(first_name='John').values('pk').query
                    ).distinct(),
            [
                "<Article: John's second story>",
                "<Article: This is a test>",
            ])
        # You need two underscores between "reporter" and "id" -- not one.
        self.assertRaises(FieldError, Article.objects.filter, reporter_id__exact=self.r.id)
        # You need to specify a comparison clause
        self.assertRaises(FieldError, Article.objects.filter, reporter_id=self.r.id)

    def test_reverse_selects(self):
        a3 = Article.objects.create(id=None, headline="Third article",
                                    pub_date=datetime(2005, 7, 27), reporter_id=self.r.id)
        a4 = Article.objects.create(id=None, headline="Fourth article",
                                    pub_date=datetime(2005, 7, 27), reporter_id=str(self.r.id))
        # Reporters can be queried
        self.assertQuerysetEqual(Reporter.objects.filter(id__exact=self.r.id),
                                 ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(Reporter.objects.filter(pk=self.r.id),
                                 ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(Reporter.objects.filter(first_name__startswith='John'),
                                 ["<Reporter: John Smith>"])
        # Reporters can query in opposite direction of ForeignKey definition
        self.assertQuerysetEqual(Reporter.objects.filter(article__id__exact=self.a.id),
                                 ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(Reporter.objects.filter(article__pk=self.a.id),
                                 ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(Reporter.objects.filter(article=self.a.id),
                                 ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(Reporter.objects.filter(article=self.a),
                                 ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__in=[self.a.id,a3.id]).distinct(),
            ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__in=[self.a.id,a3]).distinct(),
            ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__in=[self.a,a3]).distinct(),
            ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__headline__startswith='T'),
            ["<Reporter: John Smith>", "<Reporter: John Smith>"])
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__headline__startswith='T').distinct(),
            ["<Reporter: John Smith>"])

        # Counting in the opposite direction works in conjunction with distinct()
        self.assertEqual(
            Reporter.objects.filter(article__headline__startswith='T').count(), 2)
        self.assertEqual(
            Reporter.objects.filter(article__headline__startswith='T').distinct().count(), 1)

        # Queries can go round in circles.
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__reporter__first_name__startswith='John'),
            [
                "<Reporter: John Smith>",
                "<Reporter: John Smith>",
                "<Reporter: John Smith>",
            ])
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__reporter__first_name__startswith='John').distinct(),
            ["<Reporter: John Smith>"])
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__reporter__exact=self.r).distinct(),
            ["<Reporter: John Smith>"])

        # Check that implied __exact also works.
        self.assertQuerysetEqual(
            Reporter.objects.filter(article__reporter=self.r).distinct(),
            ["<Reporter: John Smith>"])

        # It's possible to use values() calls across many-to-one relations.
        # (Note, too, that we clear the ordering here so as not to drag the
        # 'headline' field into the columns being used to determine uniqueness)
        d = {'reporter__first_name': u'John', 'reporter__last_name': u'Smith'}
        self.assertEqual([d],
            list(Article.objects.filter(reporter=self.r).distinct().order_by()
                 .values('reporter__first_name', 'reporter__last_name')))

    def test_select_related(self):
        # Check that Article.objects.select_related().dates() works properly when
        # there are multiple Articles with the same date but different foreign-key
        # objects (Reporters).
        r1 = Reporter.objects.create(first_name='Mike', last_name='Royko', email='royko@suntimes.com')
        r2 = Reporter.objects.create(first_name='John', last_name='Kass', email='jkass@tribune.com')
        a1 = Article.objects.create(headline='First', pub_date=datetime(1980, 4, 23), reporter=r1)
        a2 = Article.objects.create(headline='Second', pub_date=datetime(1980, 4, 23), reporter=r2)
        self.assertEqual(list(Article.objects.select_related().dates('pub_date', 'day')),
            [
                datetime(1980, 4, 23, 0, 0),
                datetime(2005, 7, 27, 0, 0),
            ])
        self.assertEqual(list(Article.objects.select_related().dates('pub_date', 'month')),
            [
                datetime(1980, 4, 1, 0, 0),
                datetime(2005, 7, 1, 0, 0),
            ])
        self.assertEqual(list(Article.objects.select_related().dates('pub_date', 'year')),
            [
                datetime(1980, 1, 1, 0, 0),
                datetime(2005, 1, 1, 0, 0),
            ])

    def test_delete(self):
        new_article = self.r.article_set.create(headline="John's second story",
                                                pub_date=datetime(2005, 7, 29))
        new_article2 = self.r2.article_set.create(headline="Paul's story",
                                                  pub_date=datetime(2006, 1, 17))
        a3 = Article.objects.create(id=None, headline="Third article",
                                    pub_date=datetime(2005, 7, 27), reporter_id=self.r.id)
        a4 = Article.objects.create(id=None, headline="Fourth article",
                                    pub_date=datetime(2005, 7, 27), reporter_id=str(self.r.id))
        # If you delete a reporter, his articles will be deleted.
        self.assertQuerysetEqual(Article.objects.all(),
            [
                "<Article: Fourth article>",
                "<Article: John's second story>",
                "<Article: Paul's story>",
                "<Article: Third article>",
                "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(Reporter.objects.order_by('first_name'),
            [
                "<Reporter: John Smith>",
                "<Reporter: Paul Jones>",
            ])
        self.r2.delete()
        self.assertQuerysetEqual(Article.objects.all(),
            [
                "<Article: Fourth article>",
                "<Article: John's second story>",
                "<Article: Third article>",
                "<Article: This is a test>",
            ])
        self.assertQuerysetEqual(Reporter.objects.order_by('first_name'),
                                 ["<Reporter: John Smith>"])
        # You can delete using a JOIN in the query.
        Reporter.objects.filter(article__headline__startswith='This').delete()
        self.assertQuerysetEqual(Reporter.objects.all(), [])
        self.assertQuerysetEqual(Article.objects.all(), [])

    def test_regression_12876(self):
        # Regression for #12876 -- Model methods that include queries that
        # recursive don't cause recursion depth problems under deepcopy.
        self.r.cached_query = Article.objects.filter(reporter=self.r)
        from copy import deepcopy
        self.assertEqual(repr(deepcopy(self.r)), "<Reporter: John Smith>")
