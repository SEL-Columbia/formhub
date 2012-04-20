# -*- coding: utf-8 -*-
import datetime
import tempfile
import os

from django.contrib import admin
from django.core.files.storage import FileSystemStorage
from django.contrib.admin.views.main import ChangeList
from django.core.mail import EmailMessage
from django.db import models
from django import forms
from django.forms.models import BaseModelFormSet
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

class Section(models.Model):
    """
    A simple section that links to articles, to test linking to related items
    in admin views.
    """
    name = models.CharField(max_length=100)

class Article(models.Model):
    """
    A simple article to test admin views. Test backwards compatibility.
    """
    title = models.CharField(max_length=100)
    content = models.TextField()
    date = models.DateTimeField()
    section = models.ForeignKey(Section, null=True, blank=True)

    def __unicode__(self):
        return self.title

    def model_year(self):
        return self.date.year
    model_year.admin_order_field = 'date'
    model_year.short_description = ''

class Book(models.Model):
    """
    A simple book that has chapters.
    """
    name = models.CharField(max_length=100, verbose_name=u'¿Name?')

    def __unicode__(self):
        return self.name

class Promo(models.Model):
    name = models.CharField(max_length=100, verbose_name=u'¿Name?')
    book = models.ForeignKey(Book)

    def __unicode__(self):
        return self.name

class Chapter(models.Model):
    title = models.CharField(max_length=100, verbose_name=u'¿Title?')
    content = models.TextField()
    book = models.ForeignKey(Book)

    def __unicode__(self):
        return self.title

    class Meta:
        # Use a utf-8 bytestring to ensure it works (see #11710)
        verbose_name = '¿Chapter?'

class ChapterXtra1(models.Model):
    chap = models.OneToOneField(Chapter, verbose_name=u'¿Chap?')
    xtra = models.CharField(max_length=100, verbose_name=u'¿Xtra?')

    def __unicode__(self):
        return u'¿Xtra1: %s' % self.xtra

class ChapterXtra2(models.Model):
    chap = models.OneToOneField(Chapter, verbose_name=u'¿Chap?')
    xtra = models.CharField(max_length=100, verbose_name=u'¿Xtra?')

    def __unicode__(self):
        return u'¿Xtra2: %s' % self.xtra

def callable_year(dt_value):
    return dt_value.year
callable_year.admin_order_field = 'date'

class ArticleInline(admin.TabularInline):
    model = Article

class ChapterInline(admin.TabularInline):
    model = Chapter

class ChapterXtra1Admin(admin.ModelAdmin):
    list_filter = ('chap',
                   'chap__title',
                   'chap__book',
                   'chap__book__name',
                   'chap__book__promo',
                   'chap__book__promo__name',)

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('content', 'date', callable_year, 'model_year', 'modeladmin_year')
    list_filter = ('date', 'section')

    def changelist_view(self, request):
        "Test that extra_context works"
        return super(ArticleAdmin, self).changelist_view(
            request, extra_context={
                'extra_var': 'Hello!'
            }
        )

    def modeladmin_year(self, obj):
        return obj.date.year
    modeladmin_year.admin_order_field = 'date'
    modeladmin_year.short_description = None

    def delete_model(self, request, obj):
        EmailMessage(
            'Greetings from a deleted object',
            'I hereby inform you that some user deleted me',
            'from@example.com',
            ['to@example.com']
        ).send()
        return super(ArticleAdmin, self).delete_model(request, obj)

    def save_model(self, request, obj, form, change=True):
        EmailMessage(
            'Greetings from a created object',
            'I hereby inform you that some user created me',
            'from@example.com',
            ['to@example.com']
        ).send()
        return super(ArticleAdmin, self).save_model(request, obj, form, change)

class RowLevelChangePermissionModel(models.Model):
    name = models.CharField(max_length=100, blank=True)

class RowLevelChangePermissionModelAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        """ Only allow changing objects with even id number """
        return request.user.is_staff and (obj is not None) and (obj.id % 2 == 0)

class CustomArticle(models.Model):
    content = models.TextField()
    date = models.DateTimeField()

class CustomArticleAdmin(admin.ModelAdmin):
    """
    Tests various hooks for using custom templates and contexts.
    """
    change_list_template = 'custom_admin/change_list.html'
    change_form_template = 'custom_admin/change_form.html'
    add_form_template = 'custom_admin/add_form.html'
    object_history_template = 'custom_admin/object_history.html'
    delete_confirmation_template = 'custom_admin/delete_confirmation.html'
    delete_selected_confirmation_template = 'custom_admin/delete_selected_confirmation.html'

    def changelist_view(self, request):
        "Test that extra_context works"
        return super(CustomArticleAdmin, self).changelist_view(
            request, extra_context={
                'extra_var': 'Hello!'
            }
        )

class ModelWithStringPrimaryKey(models.Model):
    id = models.CharField(max_length=255, primary_key=True)

    def __unicode__(self):
        return self.id

class Color(models.Model):
    value = models.CharField(max_length=10)
    warm = models.BooleanField()
    def __unicode__(self):
        return self.value

class Thing(models.Model):
    title = models.CharField(max_length=20)
    color = models.ForeignKey(Color, limit_choices_to={'warm': True})
    def __unicode__(self):
        return self.title

class ThingAdmin(admin.ModelAdmin):
    list_filter = ('color__warm', 'color__value')

class Actor(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField()
    def __unicode__(self):
        return self.name

class Inquisition(models.Model):
    expected = models.BooleanField()
    leader = models.ForeignKey(Actor)
    country = models.CharField(max_length=20)

    def __unicode__(self):
        return u"by %s from %s" % (self.leader, self.country)

class InquisitionAdmin(admin.ModelAdmin):
    list_display = ('leader', 'country', 'expected')

class Sketch(models.Model):
    title = models.CharField(max_length=100)
    inquisition = models.ForeignKey(Inquisition, limit_choices_to={'leader__name': 'Palin',
                                                                   'leader__age': 27,
                                                                   'expected': False,
                                                                   })

    def __unicode__(self):
        return self.title

class SketchAdmin(admin.ModelAdmin):
    raw_id_fields = ('inquisition',)

class Fabric(models.Model):
    NG_CHOICES = (
        ('Textured', (
                ('x', 'Horizontal'),
                ('y', 'Vertical'),
            )
        ),
        ('plain', 'Smooth'),
    )
    surface = models.CharField(max_length=20, choices=NG_CHOICES)

class FabricAdmin(admin.ModelAdmin):
    list_display = ('surface',)
    list_filter = ('surface',)

class Person(models.Model):
    GENDER_CHOICES = (
        (1, "Male"),
        (2, "Female"),
    )
    name = models.CharField(max_length=100)
    gender = models.IntegerField(choices=GENDER_CHOICES)
    age = models.IntegerField(default=21)
    alive = models.BooleanField()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["id"]

class BasePersonModelFormSet(BaseModelFormSet):
    def clean(self):
        for person_dict in self.cleaned_data:
            person = person_dict.get('id')
            alive = person_dict.get('alive')
            if person and alive and person.name == "Grace Hopper":
                raise forms.ValidationError("Grace is not a Zombie")

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'alive')
    list_editable = ('gender', 'alive')
    list_filter = ('gender',)
    search_fields = ('^name',)
    ordering = ["id"]
    save_as = True

    def get_changelist_formset(self, request, **kwargs):
        return super(PersonAdmin, self).get_changelist_formset(request,
            formset=BasePersonModelFormSet, **kwargs)


class Persona(models.Model):
    """
    A simple persona associated with accounts, to test inlining of related
    accounts which inherit from a common accounts class.
    """
    name = models.CharField(blank=False,  max_length=80)
    def __unicode__(self):
        return self.name

class Account(models.Model):
    """
    A simple, generic account encapsulating the information shared by all
    types of accounts.
    """
    username = models.CharField(blank=False,  max_length=80)
    persona = models.ForeignKey(Persona, related_name="accounts")
    servicename = u'generic service'

    def __unicode__(self):
        return "%s: %s" % (self.servicename, self.username)

class FooAccount(Account):
    """A service-specific account of type Foo."""
    servicename = u'foo'

class BarAccount(Account):
    """A service-specific account of type Bar."""
    servicename = u'bar'

class FooAccountAdmin(admin.StackedInline):
    model = FooAccount
    extra = 1

class BarAccountAdmin(admin.StackedInline):
    model = BarAccount
    extra = 1

class PersonaAdmin(admin.ModelAdmin):
    inlines = (
        FooAccountAdmin,
        BarAccountAdmin
    )

class Subscriber(models.Model):
    name = models.CharField(blank=False, max_length=80)
    email = models.EmailField(blank=False, max_length=175)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.email)

class SubscriberAdmin(admin.ModelAdmin):
    actions = ['mail_admin']

    def mail_admin(self, request, selected):
        EmailMessage(
            'Greetings from a ModelAdmin action',
            'This is the test email from a admin action',
            'from@example.com',
            ['to@example.com']
        ).send()

class ExternalSubscriber(Subscriber):
    pass

class OldSubscriber(Subscriber):
    pass

def external_mail(modeladmin, request, selected):
    EmailMessage(
        'Greetings from a function action',
        'This is the test email from a function action',
        'from@example.com',
        ['to@example.com']
    ).send()

def redirect_to(modeladmin, request, selected):
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect('/some-where-else/')

class ExternalSubscriberAdmin(admin.ModelAdmin):
    actions = [external_mail, redirect_to]

class Media(models.Model):
    name = models.CharField(max_length=60)

class Podcast(Media):
    release_date = models.DateField()

class PodcastAdmin(admin.ModelAdmin):
    list_display = ('name', 'release_date')
    list_editable = ('release_date',)
    date_hierarchy = 'release_date'
    ordering = ('name',)

class Vodcast(Media):
    media = models.OneToOneField(Media, primary_key=True, parent_link=True)
    released = models.BooleanField(default=False)

class VodcastAdmin(admin.ModelAdmin):
    list_display = ('name', 'released')
    list_editable = ('released',)

    ordering = ('name',)

class Parent(models.Model):
    name = models.CharField(max_length=128)

class Child(models.Model):
    parent = models.ForeignKey(Parent, editable=False)
    name = models.CharField(max_length=30, blank=True)

class ChildInline(admin.StackedInline):
    model = Child

class ParentAdmin(admin.ModelAdmin):
    model = Parent
    inlines = [ChildInline]

class EmptyModel(models.Model):
    def __unicode__(self):
        return "Primary key = %s" % self.id

class EmptyModelAdmin(admin.ModelAdmin):
    def queryset(self, request):
        return super(EmptyModelAdmin, self).queryset(request).filter(pk__gt=1)

class OldSubscriberAdmin(admin.ModelAdmin):
    actions = None

temp_storage = FileSystemStorage(tempfile.mkdtemp())
UPLOAD_TO = os.path.join(temp_storage.location, 'test_upload')

class Gallery(models.Model):
    name = models.CharField(max_length=100)

class Picture(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(storage=temp_storage, upload_to='test_upload')
    gallery = models.ForeignKey(Gallery, related_name="pictures")

class PictureInline(admin.TabularInline):
    model = Picture
    extra = 1

class GalleryAdmin(admin.ModelAdmin):
    inlines = [PictureInline]

class PictureAdmin(admin.ModelAdmin):
    pass

class Language(models.Model):
    iso = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=50)
    english_name = models.CharField(max_length=50)
    shortlist = models.BooleanField(default=False)

    class Meta:
        ordering = ('iso',)

class LanguageAdmin(admin.ModelAdmin):
    list_display = ['iso', 'shortlist', 'english_name', 'name']
    list_editable = ['shortlist']

# a base class for Recommender and Recommendation
class Title(models.Model):
    pass

class TitleTranslation(models.Model):
    title = models.ForeignKey(Title)
    text = models.CharField(max_length=100)

class Recommender(Title):
    pass

class Recommendation(Title):
    recommender = models.ForeignKey(Recommender)

class RecommendationAdmin(admin.ModelAdmin):
    search_fields = ('=titletranslation__text', '=recommender__titletranslation__text',)

class Collector(models.Model):
    name = models.CharField(max_length=100)

class Widget(models.Model):
    owner = models.ForeignKey(Collector)
    name = models.CharField(max_length=100)

class DooHickey(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    owner = models.ForeignKey(Collector)
    name = models.CharField(max_length=100)

class Grommet(models.Model):
    code = models.AutoField(primary_key=True)
    owner = models.ForeignKey(Collector)
    name = models.CharField(max_length=100)

class Whatsit(models.Model):
    index = models.IntegerField(primary_key=True)
    owner = models.ForeignKey(Collector)
    name = models.CharField(max_length=100)

class Doodad(models.Model):
    name = models.CharField(max_length=100)

class FancyDoodad(Doodad):
    owner = models.ForeignKey(Collector)
    expensive = models.BooleanField(default=True)

class WidgetInline(admin.StackedInline):
    model = Widget

class DooHickeyInline(admin.StackedInline):
    model = DooHickey

class GrommetInline(admin.StackedInline):
    model = Grommet

class WhatsitInline(admin.StackedInline):
    model = Whatsit

class FancyDoodadInline(admin.StackedInline):
    model = FancyDoodad

class Category(models.Model):
    collector = models.ForeignKey(Collector)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return u'%s:o%s' % (self.id, self.order)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'collector', 'order')
    list_editable = ('order',)

class CategoryInline(admin.StackedInline):
    model = Category

class CollectorAdmin(admin.ModelAdmin):
    inlines = [
        WidgetInline, DooHickeyInline, GrommetInline, WhatsitInline,
        FancyDoodadInline, CategoryInline
    ]

class Link(models.Model):
    posted = models.DateField(
        default=lambda: datetime.date.today() - datetime.timedelta(days=7)
    )
    url = models.URLField()
    post = models.ForeignKey("Post")


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1

    readonly_fields = ("posted",)


class Post(models.Model):
    title = models.CharField(max_length=100, help_text="Some help text for the title (with unicode ŠĐĆŽćžšđ)")
    content = models.TextField(help_text="Some help text for the content (with unicode ŠĐĆŽćžšđ)")
    posted = models.DateField(
            default=datetime.date.today,
            help_text="Some help text for the date (with unicode ŠĐĆŽćžšđ)"
    )
    public = models.NullBooleanField()

    def awesomeness_level(self):
        return "Very awesome."

class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'public']
    readonly_fields = ('posted', 'awesomeness_level', 'coolness', 'value', lambda obj: "foo")

    inlines = [
        LinkInline
    ]

    def coolness(self, instance):
        if instance.pk:
            return "%d amount of cool." % instance.pk
        else:
            return "Unkown coolness."

    def value(self, instance):
        return 1000
    value.short_description = 'Value in $US'

class Gadget(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class CustomChangeList(ChangeList):
    def get_query_set(self):
        return self.root_query_set.filter(pk=9999) # Does not exist

class GadgetAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return CustomChangeList

class Villain(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class SuperVillain(Villain):
    pass

class FunkyTag(models.Model):
    "Because we all know there's only one real use case for GFKs."
    name = models.CharField(max_length=25)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.name

class Plot(models.Model):
    name = models.CharField(max_length=100)
    team_leader = models.ForeignKey(Villain, related_name='lead_plots')
    contact = models.ForeignKey(Villain, related_name='contact_plots')
    tags = generic.GenericRelation(FunkyTag)

    def __unicode__(self):
        return self.name

class PlotDetails(models.Model):
    details = models.CharField(max_length=100)
    plot = models.OneToOneField(Plot)

    def __unicode__(self):
        return self.details

class SecretHideout(models.Model):
    """ Secret! Not registered with the admin! """
    location = models.CharField(max_length=100)
    villain = models.ForeignKey(Villain)

    def __unicode__(self):
        return self.location

class SuperSecretHideout(models.Model):
    """ Secret! Not registered with the admin! """
    location = models.CharField(max_length=100)
    supervillain = models.ForeignKey(SuperVillain)

    def __unicode__(self):
        return self.location

class CyclicOne(models.Model):
    name = models.CharField(max_length=25)
    two = models.ForeignKey('CyclicTwo')

    def __unicode__(self):
        return self.name

class CyclicTwo(models.Model):
    name = models.CharField(max_length=25)
    one = models.ForeignKey(CyclicOne)

    def __unicode__(self):
        return self.name

class Topping(models.Model):
    name = models.CharField(max_length=20)

class Pizza(models.Model):
    name = models.CharField(max_length=20)
    toppings = models.ManyToManyField('Topping')

class PizzaAdmin(admin.ModelAdmin):
    readonly_fields = ('toppings',)

class Album(models.Model):
    owner = models.ForeignKey(User)
    title = models.CharField(max_length=30)

class AlbumAdmin(admin.ModelAdmin):
    list_filter = ['title']

class Employee(Person):
    code = models.CharField(max_length=20)

class WorkHour(models.Model):
    datum = models.DateField()
    employee = models.ForeignKey(Employee)

class WorkHourAdmin(admin.ModelAdmin):
    list_display = ('datum', 'employee')
    list_filter = ('employee',)

class Question(models.Model):
    question = models.CharField(max_length=20)

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    answer = models.CharField(max_length=20)

    def __unicode__(self):
        return self.answer

class Reservation(models.Model):
    start_date = models.DateTimeField()
    price = models.IntegerField()


DRIVER_CHOICES = (
    (u'bill', 'Bill G'),
    (u'steve', 'Steve J'),
)

RESTAURANT_CHOICES = (
    (u'indian', u'A Taste of India'),
    (u'thai', u'Thai Pography'),
    (u'pizza', u'Pizza Mama'),
)

class FoodDelivery(models.Model):
    reference = models.CharField(max_length=100)
    driver = models.CharField(max_length=100, choices=DRIVER_CHOICES, blank=True)
    restaurant = models.CharField(max_length=100, choices=RESTAURANT_CHOICES, blank=True)

    class Meta:
        unique_together = (("driver", "restaurant"),)

class FoodDeliveryAdmin(admin.ModelAdmin):
    list_display=('reference', 'driver', 'restaurant')
    list_editable = ('driver', 'restaurant')

class Paper(models.Model):
    title = models.CharField(max_length=30)
    author = models.CharField(max_length=30, blank=True, null=True)

class CoverLetter(models.Model):
    author = models.CharField(max_length=30)
    date_written = models.DateField(null=True, blank=True)

    def __unicode__(self):
        return self.author

class PaperAdmin(admin.ModelAdmin):
    """
    A ModelAdin with a custom queryset() method that uses only(), to test
    verbose_name display in messages shown after adding Paper instances.
    """

    def queryset(self, request):
        return super(PaperAdmin, self).queryset(request).only('title')

class CoverLetterAdmin(admin.ModelAdmin):
    """
    A ModelAdin with a custom queryset() method that uses only(), to test
    verbose_name display in messages shown after adding CoverLetter instances.
    Note that the CoverLetter model defines a __unicode__ method.
    """

    def queryset(self, request):
        #return super(CoverLetterAdmin, self).queryset(request).only('author')
        return super(CoverLetterAdmin, self).queryset(request).defer('date_written')

class Story(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()

class StoryForm(forms.ModelForm):
    class Meta:
        widgets = {'title': forms.HiddenInput}

class StoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content')
    list_display_links = ('title',) # 'id' not in list_display_links
    list_editable = ('content', )
    form = StoryForm

class OtherStory(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()

class OtherStoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content')
    list_display_links = ('title', 'id') # 'id' in list_display_links
    list_editable = ('content', )

admin.site.register(Article, ArticleAdmin)
admin.site.register(CustomArticle, CustomArticleAdmin)
admin.site.register(Section, save_as=True, inlines=[ArticleInline])
admin.site.register(ModelWithStringPrimaryKey)
admin.site.register(Color)
admin.site.register(Thing, ThingAdmin)
admin.site.register(Actor)
admin.site.register(Inquisition, InquisitionAdmin)
admin.site.register(Sketch, SketchAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Persona, PersonaAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(ExternalSubscriber, ExternalSubscriberAdmin)
admin.site.register(OldSubscriber, OldSubscriberAdmin)
admin.site.register(Podcast, PodcastAdmin)
admin.site.register(Vodcast, VodcastAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(EmptyModel, EmptyModelAdmin)
admin.site.register(Fabric, FabricAdmin)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Picture, PictureAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(Recommendation, RecommendationAdmin)
admin.site.register(Recommender)
admin.site.register(Collector, CollectorAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Gadget, GadgetAdmin)
admin.site.register(Villain)
admin.site.register(SuperVillain)
admin.site.register(Plot)
admin.site.register(PlotDetails)
admin.site.register(CyclicOne)
admin.site.register(CyclicTwo)
admin.site.register(WorkHour, WorkHourAdmin)
admin.site.register(Reservation)
admin.site.register(FoodDelivery, FoodDeliveryAdmin)
admin.site.register(RowLevelChangePermissionModel, RowLevelChangePermissionModelAdmin)
admin.site.register(Paper, PaperAdmin)
admin.site.register(CoverLetter, CoverLetterAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(OtherStory, OtherStoryAdmin)

# We intentionally register Promo and ChapterXtra1 but not Chapter nor ChapterXtra2.
# That way we cover all four cases:
#     related ForeignKey object registered in admin
#     related ForeignKey object not registered in admin
#     related OneToOne object registered in admin
#     related OneToOne object not registered in admin
# when deleting Book so as exercise all four troublesome (w.r.t escaping
# and calling force_unicode to avoid problems on Python 2.3) paths through
# contrib.admin.util's get_deleted_objects function.
admin.site.register(Book, inlines=[ChapterInline])
admin.site.register(Promo)
admin.site.register(ChapterXtra1, ChapterXtra1Admin)
admin.site.register(Pizza, PizzaAdmin)
admin.site.register(Topping)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Question)
admin.site.register(Answer)
