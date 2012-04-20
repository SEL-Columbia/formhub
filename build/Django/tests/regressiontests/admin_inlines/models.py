"""
Testing of admin inline formsets.

"""
from django.db import models
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django import forms

class Parent(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class Teacher(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class Child(models.Model):
    name = models.CharField(max_length=50)
    teacher = models.ForeignKey(Teacher)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey()

    def __unicode__(self):
        return u'I am %s, a child of %s' % (self.name, self.parent)

class Book(models.Model):
    name = models.CharField(max_length=50)

class Author(models.Model):
    name = models.CharField(max_length=50)
    books = models.ManyToManyField(Book)

class BookInline(admin.TabularInline):
    model = Author.books.through

class AuthorAdmin(admin.ModelAdmin):
    inlines = [BookInline]

admin.site.register(Author, AuthorAdmin)

class Holder(models.Model):
    dummy = models.IntegerField()


class Inner(models.Model):
    dummy = models.IntegerField()
    holder = models.ForeignKey(Holder)
    readonly = models.CharField("Inner readonly label", max_length=1)


class InnerInline(admin.StackedInline):
    model = Inner
    can_delete = False
    readonly_fields = ('readonly',) # For bug #13174 tests.


class Holder2(models.Model):
    dummy = models.IntegerField()


class Inner2(models.Model):
    dummy = models.IntegerField()
    holder = models.ForeignKey(Holder2)

class HolderAdmin(admin.ModelAdmin):

    class Media:
        js = ('my_awesome_admin_scripts.js',)

class InnerInline2(admin.StackedInline):
    model = Inner2

    class Media:
        js = ('my_awesome_inline_scripts.js',)

class Holder3(models.Model):
    dummy = models.IntegerField()


class Inner3(models.Model):
    dummy = models.IntegerField()
    holder = models.ForeignKey(Holder3)

class InnerInline3(admin.StackedInline):
    model = Inner3

    class Media:
        js = ('my_awesome_inline_scripts.js',)

# Test bug #12561 and #12778
# only ModelAdmin media
admin.site.register(Holder, HolderAdmin, inlines=[InnerInline])
# ModelAdmin and Inline media
admin.site.register(Holder2, HolderAdmin, inlines=[InnerInline2])
# only Inline media
admin.site.register(Holder3, inlines=[InnerInline3])

# Models for #12749

class Person(models.Model):
    firstname = models.CharField(max_length=15)

class OutfitItem(models.Model):
    name = models.CharField(max_length=15)

class Fashionista(models.Model):
    person = models.OneToOneField(Person, primary_key=True)
    weaknesses = models.ManyToManyField(OutfitItem, through='ShoppingWeakness', blank=True)

class ShoppingWeakness(models.Model):
    fashionista = models.ForeignKey(Fashionista)
    item = models.ForeignKey(OutfitItem)

class InlineWeakness(admin.TabularInline):
    model = ShoppingWeakness
    extra = 1

admin.site.register(Fashionista, inlines=[InlineWeakness])

# Models for #13510

class TitleCollection(models.Model):
    pass

class Title(models.Model):
    collection = models.ForeignKey(TitleCollection, blank=True, null=True)
    title1 = models.CharField(max_length=100)
    title2 = models.CharField(max_length=100)

class TitleForm(forms.ModelForm):

    def clean(self):
        cleaned_data = self.cleaned_data
        title1 = cleaned_data.get("title1")
        title2 = cleaned_data.get("title2")
        if title1 != title2:
            raise forms.ValidationError("The two titles must be the same")
        return cleaned_data

class TitleInline(admin.TabularInline):
    model = Title
    form = TitleForm
    extra = 1

admin.site.register(TitleCollection, inlines=[TitleInline])

# Models for #15424

class Poll(models.Model):
    name = models.CharField(max_length=40)

class Question(models.Model):
    poll = models.ForeignKey(Poll)

class QuestionInline(admin.TabularInline):
    model = Question
    readonly_fields=['call_me']

    def call_me(self, obj):
        return 'Callable in QuestionInline'

class PollAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]

    def call_me(self, obj):
        return 'Callable in PollAdmin'

class Novel(models.Model):
    name = models.CharField(max_length=40)

class Chapter(models.Model):
    novel = models.ForeignKey(Novel)

class ChapterInline(admin.TabularInline):
    model = Chapter
    readonly_fields=['call_me']

    def call_me(self, obj):
        return 'Callable in ChapterInline'

class NovelAdmin(admin.ModelAdmin):
    inlines = [ChapterInline]

admin.site.register(Poll, PollAdmin)
admin.site.register(Novel, NovelAdmin)
