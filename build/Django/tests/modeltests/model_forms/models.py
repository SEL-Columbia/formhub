"""
XX. Generating HTML forms from models

This is mostly just a reworking of the ``form_for_model``/``form_for_instance``
tests to use ``ModelForm``. As such, the text may not make sense in all cases,
and the examples are probably a poor fit for the ``ModelForm`` syntax. In other
words, most of these tests should be rewritten.
"""

import os
import tempfile

from django.db import models
from django.core.files.storage import FileSystemStorage

temp_storage_dir = tempfile.mkdtemp()
temp_storage = FileSystemStorage(temp_storage_dir)

ARTICLE_STATUS = (
    (1, 'Draft'),
    (2, 'Pending'),
    (3, 'Live'),
)

ARTICLE_STATUS_CHAR = (
    ('d', 'Draft'),
    ('p', 'Pending'),
    ('l', 'Live'),
)

class Category(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20)
    url = models.CharField('The URL', max_length=40)

    def __unicode__(self):
        return self.name

class Writer(models.Model):
    name = models.CharField(max_length=50, help_text='Use both first and last names.')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

class Article(models.Model):
    headline = models.CharField(max_length=50)
    slug = models.SlugField()
    pub_date = models.DateField()
    created = models.DateField(editable=False)
    writer = models.ForeignKey(Writer)
    article = models.TextField()
    categories = models.ManyToManyField(Category, blank=True)
    status = models.PositiveIntegerField(choices=ARTICLE_STATUS, blank=True, null=True)

    def save(self):
        import datetime
        if not self.id:
            self.created = datetime.date.today()
        return super(Article, self).save()

    def __unicode__(self):
        return self.headline

class ImprovedArticle(models.Model):
    article = models.OneToOneField(Article)

class ImprovedArticleWithParentLink(models.Model):
    article = models.OneToOneField(Article, parent_link=True)

class BetterWriter(Writer):
    score = models.IntegerField()

class WriterProfile(models.Model):
    writer = models.OneToOneField(Writer, primary_key=True)
    age = models.PositiveIntegerField()

    def __unicode__(self):
        return "%s is %s" % (self.writer, self.age)

from django.contrib.localflavor.us.models import PhoneNumberField
class PhoneNumber(models.Model):
    phone = PhoneNumberField()
    description = models.CharField(max_length=20)

    def __unicode__(self):
        return self.phone

class TextFile(models.Model):
    description = models.CharField(max_length=20)
    file = models.FileField(storage=temp_storage, upload_to='tests', max_length=15)

    def __unicode__(self):
        return self.description

try:
    # If PIL is available, try testing ImageFields. Checking for the existence
    # of Image is enough for CPython, but for PyPy, you need to check for the
    # underlying modules If PIL is not available, ImageField tests are omitted.
    # Try to import PIL in either of the two ways it can end up installed.
    try:
        from PIL import Image, _imaging
    except ImportError:
        import Image, _imaging

    test_images = True

    class ImageFile(models.Model):
        def custom_upload_path(self, filename):
            path = self.path or 'tests'
            return '%s/%s' % (path, filename)

        description = models.CharField(max_length=20)

        # Deliberately put the image field *after* the width/height fields to
        # trigger the bug in #10404 with width/height not getting assigned.
        width = models.IntegerField(editable=False)
        height = models.IntegerField(editable=False)
        image = models.ImageField(storage=temp_storage, upload_to=custom_upload_path,
                                  width_field='width', height_field='height')
        path = models.CharField(max_length=16, blank=True, default='')

        def __unicode__(self):
            return self.description

    class OptionalImageFile(models.Model):
        def custom_upload_path(self, filename):
            path = self.path or 'tests'
            return '%s/%s' % (path, filename)

        description = models.CharField(max_length=20)
        image = models.ImageField(storage=temp_storage, upload_to=custom_upload_path,
                                  width_field='width', height_field='height',
                                  blank=True, null=True)
        width = models.IntegerField(editable=False, null=True)
        height = models.IntegerField(editable=False, null=True)
        path = models.CharField(max_length=16, blank=True, default='')

        def __unicode__(self):
            return self.description
except ImportError:
    test_images = False

class CommaSeparatedInteger(models.Model):
    field = models.CommaSeparatedIntegerField(max_length=20)

    def __unicode__(self):
        return self.field

class Product(models.Model):
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.slug

class Price(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __unicode__(self):
        return u"%s for %s" % (self.quantity, self.price)

    class Meta:
        unique_together = (('price', 'quantity'),)

class ArticleStatus(models.Model):
    status = models.CharField(max_length=2, choices=ARTICLE_STATUS_CHAR, blank=True, null=True)

class Inventory(models.Model):
    barcode = models.PositiveIntegerField(unique=True)
    parent = models.ForeignKey('self', to_field='barcode', blank=True, null=True)
    name = models.CharField(blank=False, max_length=20)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=40)
    author = models.ForeignKey(Writer, blank=True, null=True)
    special_id = models.IntegerField(blank=True, null=True, unique=True)

    class Meta:
        unique_together = ('title', 'author')

class BookXtra(models.Model):
    isbn = models.CharField(max_length=16, unique=True)
    suffix1 = models.IntegerField(blank=True, default=0)
    suffix2 = models.IntegerField(blank=True, default=0)

    class Meta:
        unique_together = (('suffix1', 'suffix2'))
        abstract = True

class DerivedBook(Book, BookXtra):
    pass

class ExplicitPK(models.Model):
    key = models.CharField(max_length=20, primary_key=True)
    desc = models.CharField(max_length=20, blank=True, unique=True)
    class Meta:
        unique_together = ('key', 'desc')

    def __unicode__(self):
        return self.key

class Post(models.Model):
    title = models.CharField(max_length=50, unique_for_date='posted', blank=True)
    slug = models.CharField(max_length=50, unique_for_year='posted', blank=True)
    subtitle = models.CharField(max_length=50, unique_for_month='posted', blank=True)
    posted = models.DateField()

    def __unicode__(self):
        return self.name

class DerivedPost(Post):
    pass

class BigInt(models.Model):
    biggie = models.BigIntegerField()

    def __unicode__(self):
        return unicode(self.biggie)

class MarkupField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 20
        super(MarkupField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        # don't allow this field to be used in form (real use-case might be
        # that you know the markup will always be X, but it is among an app
        # that allows the user to say it could be something else)
        # regressed at r10062
        return None

class CustomFieldForExclusionModel(models.Model):
    name = models.CharField(max_length=10)
    markup = MarkupField()

class FlexibleDatePost(models.Model):
    title = models.CharField(max_length=50, unique_for_date='posted', blank=True)
    slug = models.CharField(max_length=50, unique_for_year='posted', blank=True)
    subtitle = models.CharField(max_length=50, unique_for_month='posted', blank=True)
    posted = models.DateField(blank=True, null=True)

__test__ = {'API_TESTS': """
>>> from django import forms
>>> from django.forms.models import ModelForm, model_to_dict
>>> from django.core.files.uploadedfile import SimpleUploadedFile

The bare bones, absolutely nothing custom, basic case.

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category
>>> CategoryForm.base_fields.keys()
['name', 'slug', 'url']


Extra fields.

>>> class CategoryForm(ModelForm):
...     some_extra_field = forms.BooleanField()
...
...     class Meta:
...         model = Category

>>> CategoryForm.base_fields.keys()
['name', 'slug', 'url', 'some_extra_field']

Extra field that has a name collision with a related object accessor.

>>> class WriterForm(ModelForm):
...     book = forms.CharField(required=False)
...
...     class Meta:
...         model = Writer

>>> wf = WriterForm({'name': 'Richard Lockridge'})
>>> wf.is_valid()
True

Replacing a field.

>>> class CategoryForm(ModelForm):
...     url = forms.BooleanField()
...
...     class Meta:
...         model = Category

>>> CategoryForm.base_fields['url'].__class__
<class 'django.forms.fields.BooleanField'>


Using 'fields'.

>>> class CategoryForm(ModelForm):
...
...     class Meta:
...         model = Category
...         fields = ['url']

>>> CategoryForm.base_fields.keys()
['url']


Using 'exclude'

>>> class CategoryForm(ModelForm):
...
...     class Meta:
...         model = Category
...         exclude = ['url']

>>> CategoryForm.base_fields.keys()
['name', 'slug']


Using 'fields' *and* 'exclude'. Not sure why you'd want to do this, but uh,
"be liberal in what you accept" and all.

>>> class CategoryForm(ModelForm):
...
...     class Meta:
...         model = Category
...         fields = ['name', 'url']
...         exclude = ['url']

>>> CategoryForm.base_fields.keys()
['name']

Using 'widgets'

>>> class CategoryForm(ModelForm):
...
...     class Meta:
...         model = Category
...         fields = ['name', 'url', 'slug']
...         widgets = {
...             'name': forms.Textarea,
...             'url': forms.TextInput(attrs={'class': 'url'})
...         }

>>> str(CategoryForm()['name'])
'<textarea id="id_name" rows="10" cols="40" name="name"></textarea>'

>>> str(CategoryForm()['url'])
'<input id="id_url" type="text" class="url" name="url" maxlength="40" />'

>>> str(CategoryForm()['slug'])
'<input id="id_slug" type="text" name="slug" maxlength="20" />'

Don't allow more than one 'model' definition in the inheritance hierarchy.
Technically, it would generate a valid form, but the fact that the resulting
save method won't deal with multiple objects is likely to trip up people not
familiar with the mechanics.

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category

>>> class OddForm(CategoryForm):
...     class Meta:
...         model = Article

OddForm is now an Article-related thing, because BadForm.Meta overrides
CategoryForm.Meta.
>>> OddForm.base_fields.keys()
['headline', 'slug', 'pub_date', 'writer', 'article', 'status', 'categories']

>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article

First class with a Meta class wins.

>>> class BadForm(ArticleForm, CategoryForm):
...     pass
>>> OddForm.base_fields.keys()
['headline', 'slug', 'pub_date', 'writer', 'article', 'status', 'categories']

Subclassing without specifying a Meta on the class will use the parent's Meta
(or the first parent in the MRO if there are multiple parent classes).

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category
>>> class SubCategoryForm(CategoryForm):
...     pass
>>> SubCategoryForm.base_fields.keys()
['name', 'slug', 'url']

We can also subclass the Meta inner class to change the fields list.

>>> class CategoryForm(ModelForm):
...     checkbox = forms.BooleanField()
...
...     class Meta:
...         model = Category
>>> class SubCategoryForm(CategoryForm):
...     class Meta(CategoryForm.Meta):
...         exclude = ['url']

>>> print SubCategoryForm()
<tr><th><label for="id_name">Name:</label></th><td><input id="id_name" type="text" name="name" maxlength="20" /></td></tr>
<tr><th><label for="id_slug">Slug:</label></th><td><input id="id_slug" type="text" name="slug" maxlength="20" /></td></tr>
<tr><th><label for="id_checkbox">Checkbox:</label></th><td><input type="checkbox" name="checkbox" id="id_checkbox" /></td></tr>

# test using fields to provide ordering to the fields
>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category
...         fields = ['url', 'name']

>>> CategoryForm.base_fields.keys()
['url', 'name']


>>> print CategoryForm()
<tr><th><label for="id_url">The URL:</label></th><td><input id="id_url" type="text" name="url" maxlength="40" /></td></tr>
<tr><th><label for="id_name">Name:</label></th><td><input id="id_name" type="text" name="name" maxlength="20" /></td></tr>

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category
...         fields = ['slug', 'url', 'name']
...         exclude = ['url']

>>> CategoryForm.base_fields.keys()
['slug', 'name']

# Old form_for_x tests #######################################################

>>> from django.forms import ModelForm, CharField
>>> import datetime

>>> Category.objects.all()
[]

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category
>>> f = CategoryForm()
>>> print f
<tr><th><label for="id_name">Name:</label></th><td><input id="id_name" type="text" name="name" maxlength="20" /></td></tr>
<tr><th><label for="id_slug">Slug:</label></th><td><input id="id_slug" type="text" name="slug" maxlength="20" /></td></tr>
<tr><th><label for="id_url">The URL:</label></th><td><input id="id_url" type="text" name="url" maxlength="40" /></td></tr>
>>> print f.as_ul()
<li><label for="id_name">Name:</label> <input id="id_name" type="text" name="name" maxlength="20" /></li>
<li><label for="id_slug">Slug:</label> <input id="id_slug" type="text" name="slug" maxlength="20" /></li>
<li><label for="id_url">The URL:</label> <input id="id_url" type="text" name="url" maxlength="40" /></li>
>>> print f['name']
<input id="id_name" type="text" name="name" maxlength="20" />

>>> f = CategoryForm(auto_id=False)
>>> print f.as_ul()
<li>Name: <input type="text" name="name" maxlength="20" /></li>
<li>Slug: <input type="text" name="slug" maxlength="20" /></li>
<li>The URL: <input type="text" name="url" maxlength="40" /></li>

>>> f = CategoryForm({'name': 'Entertainment', 'slug': 'entertainment', 'url': 'entertainment'})
>>> f.is_valid()
True
>>> f.cleaned_data['url']
u'entertainment'
>>> f.cleaned_data['name']
u'Entertainment'
>>> f.cleaned_data['slug']
u'entertainment'
>>> c1 = f.save()
>>> c1
<Category: Entertainment>
>>> Category.objects.all()
[<Category: Entertainment>]

>>> f = CategoryForm({'name': "It's a test", 'slug': 'its-test', 'url': 'test'})
>>> f.is_valid()
True
>>> f.cleaned_data['url']
u'test'
>>> f.cleaned_data['name']
u"It's a test"
>>> f.cleaned_data['slug']
u'its-test'
>>> c2 = f.save()
>>> c2
<Category: It's a test>
>>> Category.objects.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

If you call save() with commit=False, then it will return an object that
hasn't yet been saved to the database. In this case, it's up to you to call
save() on the resulting model instance.
>>> f = CategoryForm({'name': 'Third test', 'slug': 'third-test', 'url': 'third'})
>>> f.is_valid()
True
>>> f.cleaned_data['url']
u'third'
>>> f.cleaned_data['name']
u'Third test'
>>> f.cleaned_data['slug']
u'third-test'
>>> c3 = f.save(commit=False)
>>> c3
<Category: Third test>
>>> Category.objects.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]
>>> c3.save()
>>> Category.objects.order_by('name')
[<Category: Entertainment>, <Category: It's a test>, <Category: Third test>]

If you call save() with invalid data, you'll get a ValueError.
>>> f = CategoryForm({'name': '', 'slug': 'not a slug!', 'url': 'foo'})
>>> f.errors['name']
[u'This field is required.']
>>> f.errors['slug']
[u"Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens."]
>>> f.cleaned_data
Traceback (most recent call last):
...
AttributeError: 'CategoryForm' object has no attribute 'cleaned_data'
>>> f.save()
Traceback (most recent call last):
...
ValueError: The Category could not be created because the data didn't validate.
>>> f = CategoryForm({'name': '', 'slug': '', 'url': 'foo'})
>>> f.save()
Traceback (most recent call last):
...
ValueError: The Category could not be created because the data didn't validate.

Create a couple of Writers.
>>> w_royko = Writer(name='Mike Royko')
>>> w_royko.save()
>>> w_woodward = Writer(name='Bob Woodward')
>>> w_woodward.save()

ManyToManyFields are represented by a MultipleChoiceField, ForeignKeys and any
fields with the 'choices' attribute are represented by a ChoiceField.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm(auto_id=False)
>>> print f
<tr><th>Headline:</th><td><input type="text" name="headline" maxlength="50" /></td></tr>
<tr><th>Slug:</th><td><input type="text" name="slug" maxlength="50" /></td></tr>
<tr><th>Pub date:</th><td><input type="text" name="pub_date" /></td></tr>
<tr><th>Writer:</th><td><select name="writer">
<option value="" selected="selected">---------</option>
<option value="...">Bob Woodward</option>
<option value="...">Mike Royko</option>
</select></td></tr>
<tr><th>Article:</th><td><textarea rows="10" cols="40" name="article"></textarea></td></tr>
<tr><th>Status:</th><td><select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></td></tr>
<tr><th>Categories:</th><td><select multiple="multiple" name="categories">
<option value="...">Entertainment</option>
<option value="...">It&#39;s a test</option>
<option value="...">Third test</option>
</select><br /><span class="helptext"> Hold down "Control", or "Command" on a Mac, to select more than one.</span></td></tr>

You can restrict a form to a subset of the complete list of fields
by providing a 'fields' argument. If you try to save a
model created with such a form, you need to ensure that the fields
that are _not_ on the form have default values, or are allowed to have
a value of None. If a field isn't specified on a form, the object created
from the form can't provide a value for that field!
>>> class PartialArticleForm(ModelForm):
...     class Meta:
...         model = Article
...         fields = ('headline','pub_date')
>>> f = PartialArticleForm(auto_id=False)
>>> print f
<tr><th>Headline:</th><td><input type="text" name="headline" maxlength="50" /></td></tr>
<tr><th>Pub date:</th><td><input type="text" name="pub_date" /></td></tr>

When the ModelForm is passed an instance, that instance's current values are
inserted as 'initial' data in each Field.
>>> w = Writer.objects.get(name='Mike Royko')
>>> class RoykoForm(ModelForm):
...     class Meta:
...         model = Writer
>>> f = RoykoForm(auto_id=False, instance=w)
>>> print f
<tr><th>Name:</th><td><input type="text" name="name" value="Mike Royko" maxlength="50" /><br /><span class="helptext">Use both first and last names.</span></td></tr>

>>> art = Article(headline='Test article', slug='test-article', pub_date=datetime.date(1988, 1, 4), writer=w, article='Hello.')
>>> art.save()
>>> art_id_1 = art.id
>>> art_id_1 is not None
True
>>> class TestArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = TestArticleForm(auto_id=False, instance=art)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" value="Test article" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" value="test-article" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" value="1988-01-04" /></li>
<li>Writer: <select name="writer">
<option value="">---------</option>
<option value="...">Bob Woodward</option>
<option value="..." selected="selected">Mike Royko</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article">Hello.</textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="...">Entertainment</option>
<option value="...">It&#39;s a test</option>
<option value="...">Third test</option>
</select> <span class="helptext"> Hold down "Control", or "Command" on a Mac, to select more than one.</span></li>
>>> f = TestArticleForm({'headline': u'Test headline', 'slug': 'test-headline', 'pub_date': u'1984-02-06', 'writer': unicode(w_royko.pk), 'article': 'Hello.'}, instance=art)
>>> f.errors
{}
>>> f.is_valid()
True
>>> test_art = f.save()
>>> test_art.id == art_id_1
True
>>> test_art = Article.objects.get(id=art_id_1)
>>> test_art.headline
u'Test headline'

You can create a form over a subset of the available fields
by specifying a 'fields' argument to form_for_instance.
>>> class PartialArticleForm(ModelForm):
...     class Meta:
...         model = Article
...         fields=('headline', 'slug', 'pub_date')
>>> f = PartialArticleForm({'headline': u'New headline', 'slug': 'new-headline', 'pub_date': u'1988-01-04'}, auto_id=False, instance=art)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" value="New headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" value="new-headline" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" value="1988-01-04" /></li>
>>> f.is_valid()
True
>>> new_art = f.save()
>>> new_art.id == art_id_1
True
>>> new_art = Article.objects.get(id=art_id_1)
>>> new_art.headline
u'New headline'

Add some categories and test the many-to-many form output.
>>> new_art.categories.all()
[]
>>> new_art.categories.add(Category.objects.get(name='Entertainment'))
>>> new_art.categories.all()
[<Category: Entertainment>]
>>> class TestArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = TestArticleForm(auto_id=False, instance=new_art)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" value="New headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" value="new-headline" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" value="1988-01-04" /></li>
<li>Writer: <select name="writer">
<option value="">---------</option>
<option value="...">Bob Woodward</option>
<option value="..." selected="selected">Mike Royko</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article">Hello.</textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="..." selected="selected">Entertainment</option>
<option value="...">It&#39;s a test</option>
<option value="...">Third test</option>
</select> <span class="helptext"> Hold down "Control", or "Command" on a Mac, to select more than one.</span></li>

Initial values can be provided for model forms
>>> f = TestArticleForm(auto_id=False, initial={'headline': 'Your headline here', 'categories': [str(c1.id), str(c2.id)]})
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" value="Your headline here" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" /></li>
<li>Writer: <select name="writer">
<option value="" selected="selected">---------</option>
<option value="...">Bob Woodward</option>
<option value="...">Mike Royko</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article"></textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="..." selected="selected">Entertainment</option>
<option value="..." selected="selected">It&#39;s a test</option>
<option value="...">Third test</option>
</select> <span class="helptext"> Hold down "Control", or "Command" on a Mac, to select more than one.</span></li>

>>> f = TestArticleForm({'headline': u'New headline', 'slug': u'new-headline', 'pub_date': u'1988-01-04',
...     'writer': unicode(w_royko.pk), 'article': u'Hello.', 'categories': [unicode(c1.id), unicode(c2.id)]}, instance=new_art)
>>> new_art = f.save()
>>> new_art.id == art_id_1
True
>>> new_art = Article.objects.get(id=art_id_1)
>>> new_art.categories.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

Now, submit form data with no categories. This deletes the existing categories.
>>> f = TestArticleForm({'headline': u'New headline', 'slug': u'new-headline', 'pub_date': u'1988-01-04',
...     'writer': unicode(w_royko.pk), 'article': u'Hello.'}, instance=new_art)
>>> new_art = f.save()
>>> new_art.id == art_id_1
True
>>> new_art = Article.objects.get(id=art_id_1)
>>> new_art.categories.all()
[]

Create a new article, with categories, via the form.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm({'headline': u'The walrus was Paul', 'slug': u'walrus-was-paul', 'pub_date': u'1967-11-01',
...     'writer': unicode(w_royko.pk), 'article': u'Test.', 'categories': [unicode(c1.id), unicode(c2.id)]})
>>> new_art = f.save()
>>> art_id_2 = new_art.id
>>> art_id_2 not in (None, art_id_1)
True
>>> new_art = Article.objects.get(id=art_id_2)
>>> new_art.categories.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

Create a new article, with no categories, via the form.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm({'headline': u'The walrus was Paul', 'slug': u'walrus-was-paul', 'pub_date': u'1967-11-01',
...     'writer': unicode(w_royko.pk), 'article': u'Test.'})
>>> new_art = f.save()
>>> art_id_3 = new_art.id
>>> art_id_3 not in (None, art_id_1, art_id_2)
True
>>> new_art = Article.objects.get(id=art_id_3)
>>> new_art.categories.all()
[]

Create a new article, with categories, via the form, but use commit=False.
The m2m data won't be saved until save_m2m() is invoked on the form.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm({'headline': u'The walrus was Paul', 'slug': 'walrus-was-paul', 'pub_date': u'1967-11-01',
...     'writer': unicode(w_royko.pk), 'article': u'Test.', 'categories': [unicode(c1.id), unicode(c2.id)]})
>>> new_art = f.save(commit=False)

# Manually save the instance
>>> new_art.save()
>>> art_id_4 = new_art.id
>>> art_id_4 not in (None, art_id_1, art_id_2, art_id_3)
True

# The instance doesn't have m2m data yet
>>> new_art = Article.objects.get(id=art_id_4)
>>> new_art.categories.all()
[]

# Save the m2m data on the form
>>> f.save_m2m()
>>> new_art.categories.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

Here, we define a custom ModelForm. Because it happens to have the same fields as
the Category model, we can just call the form's save() to apply its changes to an
existing Category instance.
>>> class ShortCategory(ModelForm):
...     name = CharField(max_length=5)
...     slug = CharField(max_length=5)
...     url = CharField(max_length=3)
>>> cat = Category.objects.get(name='Third test')
>>> cat
<Category: Third test>
>>> cat.id == c3.id
True
>>> form = ShortCategory({'name': 'Third', 'slug': 'third', 'url': '3rd'}, instance=cat)
>>> form.save()
<Category: Third>
>>> Category.objects.get(id=c3.id)
<Category: Third>

Here, we demonstrate that choices for a ForeignKey ChoiceField are determined
at runtime, based on the data in the database when the form is displayed, not
the data in the database when the form is instantiated.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm(auto_id=False)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" /></li>
<li>Writer: <select name="writer">
<option value="" selected="selected">---------</option>
<option value="...">Bob Woodward</option>
<option value="...">Mike Royko</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article"></textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="...">Entertainment</option>
<option value="...">It&#39;s a test</option>
<option value="...">Third</option>
</select> <span class="helptext"> Hold down "Control", or "Command" on a Mac, to select more than one.</span></li>
>>> c4 = Category.objects.create(name='Fourth', url='4th')
>>> c4
<Category: Fourth>
>>> Writer.objects.create(name='Carl Bernstein')
<Writer: Carl Bernstein>
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" /></li>
<li>Writer: <select name="writer">
<option value="" selected="selected">---------</option>
<option value="...">Bob Woodward</option>
<option value="...">Carl Bernstein</option>
<option value="...">Mike Royko</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article"></textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="...">Entertainment</option>
<option value="...">It&#39;s a test</option>
<option value="...">Third</option>
<option value="...">Fourth</option>
</select> <span class="helptext"> Hold down "Control", or "Command" on a Mac, to select more than one.</span></li>

# ModelChoiceField ############################################################

>>> from django.forms import ModelChoiceField, ModelMultipleChoiceField

>>> f = ModelChoiceField(Category.objects.all())
>>> list(f.choices)
[(u'', u'---------'), (..., u'Entertainment'), (..., u"It's a test"), (..., u'Third'), (..., u'Fourth')]
>>> f.clean('')
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean(None)
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean(0)
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']
>>> f.clean(c3.id)
<Category: Third>
>>> f.clean(c2.id)
<Category: It's a test>

# Add a Category object *after* the ModelChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> c5 = Category.objects.create(name='Fifth', url='5th')
>>> c5
<Category: Fifth>
>>> f.clean(c5.id)
<Category: Fifth>

# Delete a Category object *after* the ModelChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> Category.objects.get(url='5th').delete()
>>> f.clean(c5.id)
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']

>>> f = ModelChoiceField(Category.objects.filter(pk=c1.id), required=False)
>>> print f.clean('')
None
>>> f.clean('')
>>> f.clean(str(c1.id))
<Category: Entertainment>
>>> f.clean('100')
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']

# queryset can be changed after the field is created.
>>> f.queryset = Category.objects.exclude(name='Fourth')
>>> list(f.choices)
[(u'', u'---------'), (..., u'Entertainment'), (..., u"It's a test"), (..., u'Third')]
>>> f.clean(c3.id)
<Category: Third>
>>> f.clean(c4.id)
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']

# check that we can safely iterate choices repeatedly
>>> gen_one = list(f.choices)
>>> gen_two = f.choices
>>> gen_one[2]
(..., u"It's a test")
>>> list(gen_two)
[(u'', u'---------'), (..., u'Entertainment'), (..., u"It's a test"), (..., u'Third')]

# check that we can override the label_from_instance method to print custom labels (#4620)
>>> f.queryset = Category.objects.all()
>>> f.label_from_instance = lambda obj: "category " + str(obj)
>>> list(f.choices)
[(u'', u'---------'), (..., 'category Entertainment'), (..., "category It's a test"), (..., 'category Third'), (..., 'category Fourth')]

# ModelMultipleChoiceField ####################################################

>>> f = ModelMultipleChoiceField(Category.objects.all())
>>> list(f.choices)
[(..., u'Entertainment'), (..., u"It's a test"), (..., u'Third'), (..., u'Fourth')]
>>> f.clean(None)
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean([])
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean([c1.id])
[<Category: Entertainment>]
>>> f.clean([c2.id])
[<Category: It's a test>]
>>> f.clean([str(c1.id)])
[<Category: Entertainment>]
>>> f.clean([str(c1.id), str(c2.id)])
[<Category: Entertainment>, <Category: It's a test>]
>>> f.clean([c1.id, str(c2.id)])
[<Category: Entertainment>, <Category: It's a test>]
>>> f.clean((c1.id, str(c2.id)))
[<Category: Entertainment>, <Category: It's a test>]
>>> f.clean(['100'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 100 is not one of the available choices.']
>>> f.clean('hello')
Traceback (most recent call last):
...
ValidationError: [u'Enter a list of values.']
>>> f.clean(['fail'])
Traceback (most recent call last):
...
ValidationError: [u'"fail" is not a valid value for a primary key.']

# Add a Category object *after* the ModelMultipleChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> c6 = Category.objects.create(id=6, name='Sixth', url='6th')
>>> c6
<Category: Sixth>
>>> f.clean([c6.id])
[<Category: Sixth>]

# Delete a Category object *after* the ModelMultipleChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> Category.objects.get(url='6th').delete()
>>> f.clean([c6.id])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 6 is not one of the available choices.']

>>> f = ModelMultipleChoiceField(Category.objects.all(), required=False)
>>> f.clean([])
[]
>>> f.clean(())
[]
>>> f.clean(['10'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 10 is not one of the available choices.']
>>> f.clean([str(c3.id), '10'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 10 is not one of the available choices.']
>>> f.clean([str(c1.id), '10'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 10 is not one of the available choices.']

# queryset can be changed after the field is created.
>>> f.queryset = Category.objects.exclude(name='Fourth')
>>> list(f.choices)
[(..., u'Entertainment'), (..., u"It's a test"), (..., u'Third')]
>>> f.clean([c3.id])
[<Category: Third>]
>>> f.clean([c4.id])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. ... is not one of the available choices.']
>>> f.clean([str(c3.id), str(c4.id)])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. ... is not one of the available choices.']

>>> f.queryset = Category.objects.all()
>>> f.label_from_instance = lambda obj: "multicategory " + str(obj)
>>> list(f.choices)
[(..., 'multicategory Entertainment'), (..., "multicategory It's a test"), (..., 'multicategory Third'), (..., 'multicategory Fourth')]

# OneToOneField ###############################################################

>>> class ImprovedArticleForm(ModelForm):
...     class Meta:
...         model = ImprovedArticle
>>> ImprovedArticleForm.base_fields.keys()
['article']

>>> class ImprovedArticleWithParentLinkForm(ModelForm):
...     class Meta:
...         model = ImprovedArticleWithParentLink
>>> ImprovedArticleWithParentLinkForm.base_fields.keys()
[]

>>> bw = BetterWriter(name=u'Joe Better', score=10)
>>> bw.save()
>>> sorted(model_to_dict(bw).keys())
['id', 'name', 'score', 'writer_ptr']

>>> class BetterWriterForm(ModelForm):
...     class Meta:
...         model = BetterWriter
>>> form = BetterWriterForm({'name': 'Some Name', 'score': 12})
>>> form.is_valid()
True
>>> bw2 = form.save()
>>> bw2.delete()


>>> class WriterProfileForm(ModelForm):
...     class Meta:
...         model = WriterProfile
>>> form = WriterProfileForm()
>>> print form.as_p()
<p><label for="id_writer">Writer:</label> <select name="writer" id="id_writer">
<option value="" selected="selected">---------</option>
<option value="...">Bob Woodward</option>
<option value="...">Carl Bernstein</option>
<option value="...">Joe Better</option>
<option value="...">Mike Royko</option>
</select></p>
<p><label for="id_age">Age:</label> <input type="text" name="age" id="id_age" /></p>

>>> data = {
...     'writer': unicode(w_woodward.pk),
...     'age': u'65',
... }
>>> form = WriterProfileForm(data)
>>> instance = form.save()
>>> instance
<WriterProfile: Bob Woodward is 65>

>>> form = WriterProfileForm(instance=instance)
>>> print form.as_p()
<p><label for="id_writer">Writer:</label> <select name="writer" id="id_writer">
<option value="">---------</option>
<option value="..." selected="selected">Bob Woodward</option>
<option value="...">Carl Bernstein</option>
<option value="...">Joe Better</option>
<option value="...">Mike Royko</option>
</select></p>
<p><label for="id_age">Age:</label> <input type="text" name="age" value="65" id="id_age" /></p>

# PhoneNumberField ############################################################

>>> class PhoneNumberForm(ModelForm):
...     class Meta:
...         model = PhoneNumber
>>> f = PhoneNumberForm({'phone': '(312) 555-1212', 'description': 'Assistance'})
>>> f.is_valid()
True
>>> f.cleaned_data['phone']
u'312-555-1212'
>>> f.cleaned_data['description']
u'Assistance'

# FileField ###################################################################

# File forms.

>>> class TextFileForm(ModelForm):
...     class Meta:
...         model = TextFile

# Test conditions when files is either not given or empty.

>>> f = TextFileForm(data={'description': u'Assistance'})
>>> f.is_valid()
False
>>> f = TextFileForm(data={'description': u'Assistance'}, files={})
>>> f.is_valid()
False

# Upload a file and ensure it all works as expected.

>>> f = TextFileForm(data={'description': u'Assistance'}, files={'file': SimpleUploadedFile('test1.txt', 'hello world')})
>>> f.is_valid()
True
>>> type(f.cleaned_data['file'])
<class 'django.core.files.uploadedfile.SimpleUploadedFile'>
>>> instance = f.save()
>>> instance.file
<FieldFile: tests/test1.txt>

>>> instance.file.delete()

>>> f = TextFileForm(data={'description': u'Assistance'}, files={'file': SimpleUploadedFile('test1.txt', 'hello world')})
>>> f.is_valid()
True
>>> type(f.cleaned_data['file'])
<class 'django.core.files.uploadedfile.SimpleUploadedFile'>
>>> instance = f.save()
>>> instance.file
<FieldFile: tests/test1.txt>

# Check if the max_length attribute has been inherited from the model.
>>> f = TextFileForm(data={'description': u'Assistance'}, files={'file': SimpleUploadedFile('test-maxlength.txt', 'hello world')})
>>> f.is_valid()
False

# Edit an instance that already has the file defined in the model. This will not
# save the file again, but leave it exactly as it is.

>>> f = TextFileForm(data={'description': u'Assistance'}, instance=instance)
>>> f.is_valid()
True
>>> f.cleaned_data['file']
<FieldFile: tests/test1.txt>
>>> instance = f.save()
>>> instance.file
<FieldFile: tests/test1.txt>

# Delete the current file since this is not done by Django.
>>> instance.file.delete()

# Override the file by uploading a new one.

>>> f = TextFileForm(data={'description': u'Assistance'}, files={'file': SimpleUploadedFile('test2.txt', 'hello world')}, instance=instance)
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.file
<FieldFile: tests/test2.txt>

# Delete the current file since this is not done by Django.
>>> instance.file.delete()

>>> f = TextFileForm(data={'description': u'Assistance'}, files={'file': SimpleUploadedFile('test2.txt', 'hello world')})
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.file
<FieldFile: tests/test2.txt>

# Delete the current file since this is not done by Django.
>>> instance.file.delete()

>>> instance.delete()

# Test the non-required FileField
>>> f = TextFileForm(data={'description': u'Assistance'})
>>> f.fields['file'].required = False
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.file
<FieldFile: None>

>>> f = TextFileForm(data={'description': u'Assistance'}, files={'file': SimpleUploadedFile('test3.txt', 'hello world')}, instance=instance)
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.file
<FieldFile: tests/test3.txt>

# Instance can be edited w/out re-uploading the file and existing file should be preserved.

>>> f = TextFileForm(data={'description': u'New Description'}, instance=instance)
>>> f.fields['file'].required = False
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.description
u'New Description'
>>> instance.file
<FieldFile: tests/test3.txt>

# Delete the current file since this is not done by Django.
>>> instance.file.delete()
>>> instance.delete()

>>> f = TextFileForm(data={'description': u'Assistance'}, files={'file': SimpleUploadedFile('test3.txt', 'hello world')})
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.file
<FieldFile: tests/test3.txt>

# Delete the current file since this is not done by Django.
>>> instance.file.delete()
>>> instance.delete()

# BigIntegerField ################################################################
>>> class BigIntForm(forms.ModelForm):
...     class Meta:
...         model = BigInt
...
>>> bif = BigIntForm({'biggie': '-9223372036854775808'})
>>> bif.is_valid()
True
>>> bif = BigIntForm({'biggie': '-9223372036854775809'})
>>> bif.is_valid()
False
>>> bif.errors
{'biggie': [u'Ensure this value is greater than or equal to -9223372036854775808.']}
>>> bif = BigIntForm({'biggie': '9223372036854775807'})
>>> bif.is_valid()
True
>>> bif = BigIntForm({'biggie': '9223372036854775808'})
>>> bif.is_valid()
False
>>> bif.errors
{'biggie': [u'Ensure this value is less than or equal to 9223372036854775807.']}
"""}

if test_images:
    __test__['API_TESTS'] += """
# ImageField ###################################################################

# ImageField and FileField are nearly identical, but they differ slighty when
# it comes to validation. This specifically tests that #6302 is fixed for
# both file fields and image fields.

>>> class ImageFileForm(ModelForm):
...     class Meta:
...         model = ImageFile

>>> image_data = open(os.path.join(os.path.dirname(__file__), "test.png"), 'rb').read()
>>> image_data2 = open(os.path.join(os.path.dirname(__file__), "test2.png"), 'rb').read()

>>> f = ImageFileForm(data={'description': u'An image'}, files={'image': SimpleUploadedFile('test.png', image_data)})
>>> f.is_valid()
True
>>> type(f.cleaned_data['image'])
<class 'django.core.files.uploadedfile.SimpleUploadedFile'>
>>> instance = f.save()
>>> instance.image
<...FieldFile: tests/test.png>
>>> instance.width
16
>>> instance.height
16

# Delete the current file since this is not done by Django, but don't save
# because the dimension fields are not null=True.
>>> instance.image.delete(save=False)

>>> f = ImageFileForm(data={'description': u'An image'}, files={'image': SimpleUploadedFile('test.png', image_data)})
>>> f.is_valid()
True
>>> type(f.cleaned_data['image'])
<class 'django.core.files.uploadedfile.SimpleUploadedFile'>
>>> instance = f.save()
>>> instance.image
<...FieldFile: tests/test.png>
>>> instance.width
16
>>> instance.height
16

# Edit an instance that already has the (required) image defined in the model. This will not
# save the image again, but leave it exactly as it is.

>>> f = ImageFileForm(data={'description': u'Look, it changed'}, instance=instance)
>>> f.is_valid()
True
>>> f.cleaned_data['image']
<...FieldFile: tests/test.png>
>>> instance = f.save()
>>> instance.image
<...FieldFile: tests/test.png>
>>> instance.height
16
>>> instance.width
16

# Delete the current file since this is not done by Django, but don't save
# because the dimension fields are not null=True.
>>> instance.image.delete(save=False)

# Override the file by uploading a new one.

>>> f = ImageFileForm(data={'description': u'Changed it'}, files={'image': SimpleUploadedFile('test2.png', image_data2)}, instance=instance)
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.image
<...FieldFile: tests/test2.png>
>>> instance.height
32
>>> instance.width
48

# Delete the current file since this is not done by Django, but don't save
# because the dimension fields are not null=True.
>>> instance.image.delete(save=False)
>>> instance.delete()

>>> f = ImageFileForm(data={'description': u'Changed it'}, files={'image': SimpleUploadedFile('test2.png', image_data2)})
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.image
<...FieldFile: tests/test2.png>
>>> instance.height
32
>>> instance.width
48

# Delete the current file since this is not done by Django, but don't save
# because the dimension fields are not null=True.
>>> instance.image.delete(save=False)
>>> instance.delete()

# Test the non-required ImageField

>>> class OptionalImageFileForm(ModelForm):
...     class Meta:
...         model = OptionalImageFile

>>> f = OptionalImageFileForm(data={'description': u'Test'})
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.image
<...FieldFile: None>
>>> instance.width
>>> instance.height

>>> f = OptionalImageFileForm(data={'description': u'And a final one'}, files={'image': SimpleUploadedFile('test3.png', image_data)}, instance=instance)
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.image
<...FieldFile: tests/test3.png>
>>> instance.width
16
>>> instance.height
16

# Editing the instance without re-uploading the image should not affect the image or its width/height properties
>>> f = OptionalImageFileForm(data={'description': u'New Description'}, instance=instance)
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.description
u'New Description'
>>> instance.image
<...FieldFile: tests/test3.png>
>>> instance.width
16
>>> instance.height
16

# Delete the current file since this is not done by Django.
>>> instance.image.delete()
>>> instance.delete()

>>> f = OptionalImageFileForm(data={'description': u'And a final one'}, files={'image': SimpleUploadedFile('test4.png', image_data2)})
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.image
<...FieldFile: tests/test4.png>
>>> instance.width
48
>>> instance.height
32
>>> instance.delete()

# Test callable upload_to behavior that's dependent on the value of another field in the model
>>> f = ImageFileForm(data={'description': u'And a final one', 'path': 'foo'}, files={'image': SimpleUploadedFile('test4.png', image_data)})
>>> f.is_valid()
True
>>> instance = f.save()
>>> instance.image
<...FieldFile: foo/test4.png>
>>> instance.delete()
"""

__test__['API_TESTS'] += """

# Media on a ModelForm ########################################################

# Similar to a regular Form class you can define custom media to be used on
# the ModelForm.

>>> class ModelFormWithMedia(ModelForm):
...     class Media:
...         js = ('/some/form/javascript',)
...         css = {
...             'all': ('/some/form/css',)
...         }
...     class Meta:
...         model = PhoneNumber
>>> f = ModelFormWithMedia()
>>> print f.media
<link href="/some/form/css" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/some/form/javascript"></script>

>>> class CommaSeparatedIntegerForm(ModelForm):
...    class Meta:
...        model = CommaSeparatedInteger

>>> f = CommaSeparatedIntegerForm({'field': '1,2,3'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'field': u'1,2,3'}
>>> f = CommaSeparatedIntegerForm({'field': '1a,2'})
>>> f.errors
{'field': [u'Enter only digits separated by commas.']}
>>> f = CommaSeparatedIntegerForm({'field': ',,,,'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'field': u',,,,'}
>>> f = CommaSeparatedIntegerForm({'field': '1.2'})
>>> f.errors
{'field': [u'Enter only digits separated by commas.']}
>>> f = CommaSeparatedIntegerForm({'field': '1,a,2'})
>>> f.errors
{'field': [u'Enter only digits separated by commas.']}
>>> f = CommaSeparatedIntegerForm({'field': '1,,2'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'field': u'1,,2'}
>>> f = CommaSeparatedIntegerForm({'field': '1'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'field': u'1'}

This Price instance generated by this form is not valid because the quantity
field is required, but the form is valid because the field is excluded from
the form. This is for backwards compatibility.

>>> class PriceForm(ModelForm):
...     class Meta:
...         model = Price
...         exclude = ('quantity',)
>>> form = PriceForm({'price': '6.00'})
>>> form.is_valid()
True
>>> price = form.save(commit=False)
>>> price.full_clean()
Traceback (most recent call last):
  ...
ValidationError: {'quantity': [u'This field cannot be null.']}

The form should not validate fields that it doesn't contain even if they are
specified using 'fields', not 'exclude'.
...     class Meta:
...         model = Price
...         fields = ('price',)
>>> form = PriceForm({'price': '6.00'})
>>> form.is_valid()
True

The form should still have an instance of a model that is not complete and
not saved into a DB yet.

>>> form.instance.price
Decimal('6.00')
>>> form.instance.quantity is None
True
>>> form.instance.pk is None
True

# Choices on CharField and IntegerField
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm()
>>> f.fields['status'].clean('42')
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 42 is not one of the available choices.']

>>> class ArticleStatusForm(ModelForm):
...     class Meta:
...         model = ArticleStatus
>>> f = ArticleStatusForm()
>>> f.fields['status'].clean('z')
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. z is not one of the available choices.']

# Foreign keys which use to_field #############################################

>>> apple = Inventory.objects.create(barcode=86, name='Apple')
>>> pear = Inventory.objects.create(barcode=22, name='Pear')
>>> core = Inventory.objects.create(barcode=87, name='Core', parent=apple)

>>> field = ModelChoiceField(Inventory.objects.all(), to_field_name='barcode')
>>> for choice in field.choices:
...     print choice
(u'', u'---------')
(86, u'Apple')
(87, u'Core')
(22, u'Pear')

>>> class InventoryForm(ModelForm):
...     class Meta:
...         model = Inventory
>>> form = InventoryForm(instance=core)
>>> print form['parent']
<select name="parent" id="id_parent">
<option value="">---------</option>
<option value="86" selected="selected">Apple</option>
<option value="87">Core</option>
<option value="22">Pear</option>
</select>

>>> data = model_to_dict(core)
>>> data['parent'] = '22'
>>> form = InventoryForm(data=data, instance=core)
>>> core = form.save()
>>> core.parent
<Inventory: Pear>

>>> class CategoryForm(ModelForm):
...     description = forms.CharField()
...     class Meta:
...         model = Category
...         fields = ['description', 'url']

>>> CategoryForm.base_fields.keys()
['description', 'url']

>>> print CategoryForm()
<tr><th><label for="id_description">Description:</label></th><td><input type="text" name="description" id="id_description" /></td></tr>
<tr><th><label for="id_url">The URL:</label></th><td><input id="id_url" type="text" name="url" maxlength="40" /></td></tr>

# to_field_name should also work on ModelMultipleChoiceField ##################

>>> field = ModelMultipleChoiceField(Inventory.objects.all(), to_field_name='barcode')
>>> for choice in field.choices:
...     print choice
(86, u'Apple')
(87, u'Core')
(22, u'Pear')
>>> field.clean([86])
[<Inventory: Apple>]

>>> class SelectInventoryForm(forms.Form):
...     items = ModelMultipleChoiceField(Inventory.objects.all(), to_field_name='barcode')
>>> form = SelectInventoryForm({'items': [87, 22]})
>>> form.is_valid()
True
>>> form.cleaned_data
{'items': [<Inventory: Core>, <Inventory: Pear>]}

# Model field that returns None to exclude itself with explicit fields ########

>>> class CustomFieldForExclusionForm(ModelForm):
...     class Meta:
...         model = CustomFieldForExclusionModel
...         fields = ['name', 'markup']

>>> CustomFieldForExclusionForm.base_fields.keys()
['name']

>>> print CustomFieldForExclusionForm()
<tr><th><label for="id_name">Name:</label></th><td><input id="id_name" type="text" name="name" maxlength="10" /></td></tr>

# Clean up
>>> import shutil
>>> shutil.rmtree(temp_storage_dir)
"""
