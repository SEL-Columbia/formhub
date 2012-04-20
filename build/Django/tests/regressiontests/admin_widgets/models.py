from django.db import models
from django.contrib.auth.models import User


class MyFileField(models.FileField):
    pass

class Member(models.Model):
    name = models.CharField(max_length=100)
    birthdate = models.DateTimeField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, choices=[('M','Male'), ('F', 'Female')])

    def __unicode__(self):
        return self.name

class Band(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(Member)

    def __unicode__(self):
        return self.name

class Album(models.Model):
    band = models.ForeignKey(Band)
    name = models.CharField(max_length=100)
    cover_art = models.FileField(upload_to='albums')
    backside_art = MyFileField(upload_to='albums_back', null=True)

    def __unicode__(self):
        return self.name

class HiddenInventoryManager(models.Manager):
    def get_query_set(self):
        return super(HiddenInventoryManager, self).get_query_set().filter(hidden=False)

class Inventory(models.Model):
   barcode = models.PositiveIntegerField(unique=True)
   parent = models.ForeignKey('self', to_field='barcode', blank=True, null=True)
   name = models.CharField(blank=False, max_length=20)
   hidden = models.BooleanField(default=False)

   # see #9258
   default_manager = models.Manager()
   objects = HiddenInventoryManager()

   def __unicode__(self):
      return self.name

class Event(models.Model):
    band = models.ForeignKey(Band, limit_choices_to=models.Q(pk__gt=0))
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    min_age = models.IntegerField(blank=True, null=True)

class Car(models.Model):
    owner = models.ForeignKey(User)
    make = models.CharField(max_length=30)
    model = models.CharField(max_length=30)

    def __unicode__(self):
        return u"%s %s" % (self.make, self.model)

class CarTire(models.Model):
    """
    A single car tire. This to test that a user can only select their own cars.
    """
    car = models.ForeignKey(Car)
