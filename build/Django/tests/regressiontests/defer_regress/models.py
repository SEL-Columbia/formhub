"""
Regression tests for defer() / only() behavior.
"""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models

class Item(models.Model):
    name = models.CharField(max_length=15)
    text = models.TextField(default="xyzzy")
    value = models.IntegerField()
    other_value = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

class RelatedItem(models.Model):
    item = models.ForeignKey(Item)

class Child(models.Model):
    name = models.CharField(max_length=10)
    value = models.IntegerField()

class Leaf(models.Model):
    name = models.CharField(max_length=10)
    child = models.ForeignKey(Child)
    second_child = models.ForeignKey(Child, related_name="other", null=True)
    value = models.IntegerField(default=42)

    def __unicode__(self):
        return self.name

class ResolveThis(models.Model):
    num = models.FloatField()
    name = models.CharField(max_length=16)
